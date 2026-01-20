import dash
from dash import dcc, html, Input, Output
import pandas as pd
from dash import dash_table
import plotly.graph_objs as go
from pathlib import Path
from typing import Optional, List, Dict, Any
import os
import logging
import ast

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('dashboard.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / 'data'

app = dash.Dash(__name__)
app.scripts.config.serve_locally = True
app.css.config.serve_locally = True

# ============================================================================
# DATA CACHE SYSTEM
# ============================================================================

class DataCache:
    """Cache system that invalidates when files are modified."""
    
    def __init__(self):
        self._cache = {}
        self._file_times = {}
    
    def get_data(self, filepath: str) -> pd.DataFrame:
        """
        Loads CSV data with caching.
        Cache is invalidated if the file modification time changes.
        
        Args:
            filepath: Path to the CSV file
            
        Returns:
            DataFrame with the CSV data
            
        Raises:
            FileNotFoundError: If file doesn't exist
            pd.errors.EmptyDataError: If CSV file is empty
            Exception: For other reading errors
        """
        filepath_str = str(filepath)
        
        # Check if file exists
        if not os.path.exists(filepath_str):
            logger.error(f"Data file not found: {filepath_str}")
            raise FileNotFoundError(f"Data file not found: {filepath_str}")
        
        try:
            # Get current modification time
            current_time = os.path.getmtime(filepath_str)
            
            # Check if we need to reload (file not in cache or file was modified)
            if filepath_str not in self._cache or self._file_times[filepath_str] < current_time:
                logger.info(f"Loading data from {filepath_str}")
                self._cache[filepath_str] = pd.read_csv(filepath_str)
                self._file_times[filepath_str] = current_time
                logger.info(f"Successfully cached {filepath_str}")
            
            return self._cache[filepath_str]
        
        except pd.errors.EmptyDataError:
            logger.error(f"Empty CSV file: {filepath_str}")
            raise
        except Exception as e:
            logger.error(f"Error reading {filepath_str}: {e}")
            raise
    
    def clear_cache(self):
        """Clears all cached data."""
        self._cache.clear()
        self._file_times.clear()

# Global cache instance
data_cache = DataCache()

# ============================================================================
# DATA VALIDATION
# ============================================================================

def validate_dataframe(df: pd.DataFrame, required_columns: List[str]) -> bool:
    """
    Validates that the DataFrame has all required columns.
    
    Args:
        df: DataFrame to validate
        required_columns: List of required column names
        
    Returns:
        True if all columns exist, False otherwise
    """
    if df.empty:
        logger.warning("DataFrame is empty")
        return False
    
    missing = set(required_columns) - set(df.columns)
    if missing:
        logger.error(f"Missing required columns: {missing}")
        logger.info(f"Available columns: {list(df.columns)}")
        return False
    
    return True

def load_and_validate_data(
    filepath: Path,
    required_columns: List[str],
    default_columns: Optional[List[str]] = None
) -> pd.DataFrame:
    """
    Loads data from cache and validates required columns.
    
    Args:
        filepath: Path to the CSV file
        required_columns: List of required column names
        default_columns: Optional default columns if file doesn't exist
        
    Returns:
        Validated DataFrame
        
    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If required columns are missing
    """
    try:
        df = data_cache.get_data(filepath)
        
        if not validate_dataframe(df, required_columns):
            raise ValueError(
                f"Data validation failed for {filepath}. "
                f"Missing required columns: {set(required_columns) - set(df.columns)}"
            )
        
        logger.info(f"Successfully loaded and validated {filepath}")
        return df
        
    except FileNotFoundError:
        logger.error(f"File not found: {filepath}")
        if default_columns:
            logger.warning(f"Returning empty DataFrame with default columns: {default_columns}")
            return pd.DataFrame(columns=default_columns)
        raise
    except pd.errors.EmptyDataError:
        logger.error(f"Empty CSV file: {filepath}")
        if default_columns:
            return pd.DataFrame(columns=default_columns)
        raise
    except Exception as e:
        logger.error(f"Error loading {filepath}: {str(e)}")
        raise


COLORS = {
    'primary': '#0C4A6E',
    'secondary': '#104E63',
    'success': '#2ca02c',
    'danger': '#d62728',
    'warning': '#FFB347',
    'dark': '#374151',
    'light': '#f9f9f9',
    'white': '#ffffff',
    'text': '#333333',
    'text_light': '#666666',
}

# Common styles
COMMON_STYLES = {
    'section_header': {
        'display': 'flex',
        'alignItems': 'center',
        'marginBottom': '20px',
        'color': COLORS['primary'],
        'fontSize': '24px',
        'fontWeight': 'bold'
    },
    'subsection_header': {
        'marginTop': '30px',
        'marginBottom': '15px',
        'color': COLORS['text'],
        'fontSize': '18px',
        'fontWeight': '600'
    },
    'content_container': {
        'padding': '30px',
        'backgroundColor': COLORS['white']
    },
    'graph_container': {
        'marginBottom': '30px',
        'backgroundColor': COLORS['white'],
        'padding': '20px',
        'borderRadius': '8px',
        'boxShadow': '0 2px 4px rgba(0,0,0,0.1)'
    }
}

# ============================================================================
# HELPER FUNCTIONS - REUSABLE COMPONENTS
# ============================================================================

def create_section_header(title: str, icon_class: Optional[str] = None) -> html.Div:
    """Creates a consistent section header."""
    children = [html.H2(title, style=COMMON_STYLES['section_header'])]
    if icon_class:
        children.insert(0, html.I(
            className=icon_class,
            style={'marginRight': '10px', 'fontSize': '24px'}
        ))
    return html.Div(children, style={'display': 'flex', 'alignItems': 'center'})

def create_subsection_header(title: str) -> html.H4:
    """Creates a subsection header."""
    return html.H4(title, style=COMMON_STYLES['subsection_header'])

def create_data_table(
    df: pd.DataFrame,
    page_size: int = 10,
    style_cell: Optional[Dict] = None,
    style_data: Optional[Dict] = None,
    style_header: Optional[Dict] = None,
    style_data_conditional: Optional[List] = None
) -> dash_table.DataTable:
    """Creates a data table with consistent styles."""
    
    default_style_cell = {
        'textAlign': 'left',
        'padding': '12px',
        'fontFamily': 'Arial, sans-serif',
        'fontSize': '14px',
        'border': '1px solid #e0e0e0'
    }
    
    default_style_data = {
        'backgroundColor': COLORS['white'],
        'color': COLORS['text']
    }
    
    default_style_header = {
        'backgroundColor': COLORS['dark'],
        'color': COLORS['white'],
        'fontWeight': 'bold',
        'textAlign': 'left',
        'padding': '12px',
        'fontSize': '14px',
        'border': '1px solid #374151'
    }
    
    # Merge custom styles with defaults
    final_style_cell = {**default_style_cell, **(style_cell or {})}
    final_style_data = {**default_style_data, **(style_data or {})}
    final_style_header = {**default_style_header, **(style_header or {})}
    
    return dash_table.DataTable(
        data=df.to_dict('records'),
        columns=[{'name': col, 'id': col} for col in df.columns],
        page_size=page_size,
        style_table={
            'overflowX': 'auto',
            'borderRadius': '8px',
            'boxShadow': '0 2px 4px rgba(0,0,0,0.1)',
            'marginBottom': '20px'
        },
        style_cell=final_style_cell,
        style_data=final_style_data,
        style_header=final_style_header,
        style_data_conditional=style_data_conditional or [],
        sort_action="native",
        page_action="native"
    )

def create_bar_chart(
    x_data: List,
    y_data: List,
    title: str,
    x_label: str = "",
    y_label: str = "",
    color: str = COLORS['primary'],
    height: int = 300,
    show_text: bool = False
) -> go.Figure:
    """Creates a bar chart with consistent style."""
    fig = go.Figure(data=[go.Bar(
        x=x_data,
        y=y_data,
        marker=dict(
            color=color,
            line=dict(width=1.5, color='#333')
        ),
        text=y_data if show_text else None,
        textposition='auto' if show_text else None
    )])
    
    fig.update_layout(
        title={
            'text': title,
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 20, 'color': COLORS['text']}
        },
        xaxis_title=x_label,
        yaxis_title=y_label,
        height=height,
        plot_bgcolor=COLORS['white'],
        paper_bgcolor=COLORS['white'],
        font=dict(family='Arial, sans-serif', size=12, color=COLORS['text']),
        margin=dict(l=50, r=50, t=50, b=50)
    )
    
    return fig

def create_pie_chart(
    labels: List,
    values: List,
    title: str,
    colors: Optional[List[str]] = None,
    height: int = 300
) -> go.Figure:
    """Creates a pie chart with consistent style."""
    default_colors = [COLORS['success'], COLORS['danger'], COLORS['warning'], COLORS['primary']]
    
    fig = go.Figure(data=[go.Pie(
        labels=labels,
        values=values,
        marker=dict(colors=colors or default_colors),
        textinfo='label+percent',
        textposition='outside',
        hole=0.3
    )])
    
    fig.update_layout(
        title={
            'text': title,
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 20, 'color': COLORS['text']}
        },
        height=height,
        plot_bgcolor=COLORS['white'],
        paper_bgcolor=COLORS['white'],
        font=dict(family='Arial, sans-serif', size=12, color=COLORS['text']),
        margin=dict(l=50, r=50, t=50, b=50),
        showlegend=True,
        legend=dict(
            orientation="v",
            yanchor="middle",
            y=0.5,
            xanchor="left",
            x=1.05
        )
    )
    
    return fig

def create_grouped_bar_chart(
    data: Dict[str, pd.Series],
    title: str,
    x_label: str = "",
    y_label: str = "",
    height: int = 300,
    x_tickangle: int = 0
) -> go.Figure:
    """Creates a grouped bar chart with consistent style."""
    fig = go.Figure()
    
    color_palette = [COLORS['primary'], COLORS['success'], COLORS['warning'], COLORS['danger']]
    
    for idx, (column, series) in enumerate(data.items()):
        fig.add_trace(go.Bar(
            x=series.index,
            y=series.values,
            name=column,
            text=series.values,
            textposition='auto',
            marker=dict(
                color=color_palette[idx % len(color_palette)],
                line=dict(width=1.5, color='#333')
            )
        ))
    
    fig.update_layout(
        title={
            'text': title,
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 20, 'color': COLORS['text']}
        },
        xaxis_title=x_label,
        yaxis_title=y_label,
        barmode='group',
        height=height,
        xaxis_tickangle=x_tickangle,
        plot_bgcolor=COLORS['white'],
        paper_bgcolor=COLORS['white'],
        font=dict(family='Arial, sans-serif', size=12, color=COLORS['text']),
        margin=dict(l=50, r=50, t=50, b=50),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    return fig

def create_graph_container(figure: go.Figure) -> html.Div:
    """Wraps a graph in a styled container."""
    return html.Div(
        dcc.Graph(figure=figure, config={'displayModeBar': True}),
        style=COMMON_STYLES['graph_container']
    )

def create_error_message(
    title: str,
    error: str,
    icon_class: str = 'fa-solid fa-triangle-exclamation'
) -> html.Div:
    """
    Creates a consistent error message component.
    
    Args:
        title: Title of the error section
        error: Error message to display
        icon_class: Font Awesome icon class
        
    Returns:
        HTML Div with error message
    """
    return html.Div([
        create_section_header(title, icon_class),
        html.Div([
            html.H4(
                "Error Loading Data",
                style={
                    'color': COLORS['danger'],
                    'marginBottom': '10px',
                    'fontSize': '18px'
                }
            ),
            html.P(
                error,
                style={
                    'color': COLORS['text_light'],
                    'marginBottom': '10px',
                    'fontSize': '14px'
                }
            ),
            html.P(
                "Please check the logs for more details.",
                style={
                    'color': COLORS['text_light'],
                    'fontSize': '12px',
                    'fontStyle': 'italic'
                }
            )
        ], style={
            'padding': '20px',
            'backgroundColor': COLORS['light'],
            'borderRadius': '8px',
            'border': f'2px solid {COLORS["danger"]}',
            'marginTop': '20px'
        })
    ], style=COMMON_STYLES['content_container'])

def safe_parse_ports(ports_str: str) -> List[int]:
    """
    Safely parses a string representation of ports list.
    
    Supports multiple formats:
    - Python list literal: "[22, 80, 443]"
    - Comma-separated: "22, 80, 443"
    - Already a list: [22, 80, 443]
    
    Args:
        ports_str: String or list representation of ports
        
    Returns:
        List of port numbers (integers)
    """
    if isinstance(ports_str, list):
        return [int(p) for p in ports_str if isinstance(p, (int, str)) and str(p).strip().isdigit()]
    
    ports_str = str(ports_str).strip()
    
    if not ports_str or ports_str.lower() in ['nan', 'none', '']:
        return []
    
    try:
        # Option 1: Try ast.literal_eval (safe for Python literals)
        result = ast.literal_eval(ports_str)
        if isinstance(result, list):
            return [int(p) for p in result if isinstance(p, (int, str)) and str(p).strip().isdigit()]
        elif isinstance(result, int):
            return [result]
        else:
            raise ValueError(f"Unexpected type from literal_eval: {type(result)}")
    except (ValueError, SyntaxError) as e:
        logger.debug(f"ast.literal_eval failed for '{ports_str}': {e}, trying fallback parsing")
        
        # Option 2: Fallback to comma-separated parsing
        # Remove brackets if present
        if ports_str.startswith('[') and ports_str.endswith(']'):
            ports_str = ports_str[1:-1]
        elif ports_str.startswith('(') and ports_str.endswith(')'):
            ports_str = ports_str[1:-1]
        
        # Split by comma and parse
        ports = []
        for part in ports_str.split(','):
            part = part.strip()
            if part.isdigit():
                ports.append(int(part))
        
        if ports:
            return ports
        
        # If all parsing fails, log warning and return empty list
        logger.warning(f"Could not parse ports from '{ports_str}', returning empty list")
        return []

# ============================================================================
# REPORT FUNCTIONS
# ============================================================================

def report_ips():
    """Scanned IPs report."""
    df = pd.DataFrame({'IPs': ['192.168.1.1', '10.0.0.2'], 'Count': [5, 3]})
    fig = create_bar_chart(
        x_data=df['IPs'].tolist(),
        y_data=df['Count'].tolist(),
        title='IPs Scanned',
        y_label='Count',
        show_text=True
    )
    
    return html.Div([
        create_section_header('IPs Scanned', 'fa-solid fa-network-wired'),
        create_graph_container(fig)
    ], style=COMMON_STYLES['content_container'])

def report_ports():
    """Open ports report."""
    try:
        required_columns = ['OpenPorts', 'Public_IP']
        df_users = load_and_validate_data(
            DATA_DIR / 'scan_publicips_results.csv',
            required_columns
        )

        def check_open_ports(row):
            """Safely parses OpenPorts and checks if port 22 is open."""
            open_ports = safe_parse_ports(row['OpenPorts'])
            return 'Open' if 22 in open_ports else 'Closed'

        df_users['Port22Status'] = df_users.apply(check_open_ports, axis=1)
        port_status_counts = df_users['Port22Status'].value_counts()

        fig = create_pie_chart(
            labels=port_status_counts.index.tolist(),
            values=port_status_counts.values.tolist(),
            title='Port 22 Status by Public IP',
            colors=[COLORS['success'], COLORS['danger']]
        )

        table = create_data_table(df_users)

        return html.Div([
            create_section_header('Open Ports Report', 'fa-solid fa-door-open'),
            create_graph_container(fig),
            create_subsection_header('Details of Public IPs'),
            table
        ], style=COMMON_STYLES['content_container'])
    
    except (FileNotFoundError, ValueError) as e:
        logger.error(f"Error in report_ports: {e}", exc_info=True)
        return create_error_message(
            'Open Ports Report',
            f"Failed to load or process data: {str(e)}",
            'fa-solid fa-door-open'
        )
    except Exception as e:
        logger.error(f"Unexpected error in report_ports: {e}", exc_info=True)
        return create_error_message(
            'Open Ports Report',
            f"An unexpected error occurred: {str(e)}",
            'fa-solid fa-door-open'
        )

def report_headers():
    """Security headers report."""
    try:
        required_columns = [
            'X-Content-Type-Options',
            'X-Frame-Options',
            'Content-Security-Policy',
            'Hsts'
        ]
        df_headers = load_and_validate_data(
            DATA_DIR / 'verified_headers_results.csv',
            required_columns
        )

        counts = {
            'X-Content-Type-Options': df_headers['X-Content-Type-Options'].value_counts(),
            'X-Frame-Options': df_headers['X-Frame-Options'].value_counts(),
            'Content-Security-Policy': df_headers['Content-Security-Policy'].value_counts(),
            'Hsts': df_headers['Hsts'].value_counts(),
        }

        headers_df = pd.DataFrame(counts).fillna(0).astype(int)

        fig = create_grouped_bar_chart(
            data=counts,
            title='Header Scan Results',
            x_label='Header Status',
            y_label='Count',
            x_tickangle=-45
        )

        table = create_data_table(df_headers)

        return html.Div([
            create_section_header('Header Scan Report', 'fa-solid fa-shield-halved'),
            create_graph_container(fig),
            create_subsection_header('Details of Domain Headers'),
            table
        ], style=COMMON_STYLES['content_container'])
    
    except (FileNotFoundError, ValueError) as e:
        logger.error(f"Error in report_headers: {e}", exc_info=True)
        return create_error_message(
            'Header Scan Report',
            f"Failed to load or process data: {str(e)}",
            'fa-solid fa-shield-halved'
        )
    except Exception as e:
        logger.error(f"Unexpected error in report_headers: {e}", exc_info=True)
        return create_error_message(
            'Header Scan Report',
            f"An unexpected error occurred: {str(e)}",
            'fa-solid fa-shield-halved'
        )

def report_users():
    """IAM users report."""
    try:
        required_columns = ['Groups']
        df_users = load_and_validate_data(
            DATA_DIR / 'iam_users_results.csv',
            required_columns
        )
        group_counts = df_users['Groups'].value_counts().reset_index()
        group_counts.columns = ['Group', 'Number of Users']
        
        fig = create_bar_chart(
            x_data=group_counts['Group'].tolist(),
            y_data=group_counts['Number of Users'].tolist(),
            title='Users by Group',
            x_label='Group',
            y_label='Number of Users',
            show_text=True
        )

        table = create_data_table(df_users)

        return html.Div([
            create_section_header('IAM: Users and Permissions', 'fa-solid fa-users'),
            create_graph_container(fig),
            create_subsection_header('Full Data Table'),
            table
        ], style=COMMON_STYLES['content_container'])
    
    except (FileNotFoundError, ValueError) as e:
        logger.error(f"Error in report_users: {e}", exc_info=True)
        return create_error_message(
            'IAM: Users and Permissions',
            f"Failed to load or process data: {str(e)}",
            'fa-solid fa-users'
        )
    except Exception as e:
        logger.error(f"Unexpected error in report_users: {e}", exc_info=True)
        return create_error_message(
            'IAM: Users and Permissions',
            f"An unexpected error occurred: {str(e)}",
            'fa-solid fa-users'
        )

def report_logs():
    """Logs report."""
    return html.Div([
        create_section_header('Logs Analysis', 'fa-solid fa-file-lines'),
        html.P("Análisis de logs", style={'color': COLORS['text_light']})
    ], style=COMMON_STYLES['content_container'])

# ============================================================================
# MAIN LAYOUT
# ============================================================================

app.layout = html.Div([
    html.Link(
        rel='stylesheet',
        href='https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css'
    ),
    html.Div([
        html.Div([
            html.H2(
                [
                    html.I(className='fa-solid fa-building-lock', style={'marginRight': '10px'}),
                    'Security Dashboard'
                ],
                style={'margin': '0', 'display': 'flex', 'alignItems': 'center', 'color': COLORS['white']}
            ),
        ], style={'flex': 1, 'display': 'flex', 'alignItems': 'center'}),
        html.Div([
            html.Span("Welcome", style={
                'marginRight': '15px',
                'fontSize': '20px',
                'fontWeight': 'bold',
                'alignSelf': 'center',
                'color': COLORS['white']
            }),
            html.Img(
                src='assets/img/agus.PNG',
                style={
                    'width': '55px',
                    'height': '55px',
                    'borderRadius': '50%',
                    'border': f'2px solid {COLORS["secondary"]}',
                    'verticalAlign': 'middle',
                    'margin': '5px'
                }
            ),
        ], style={'display': 'flex', 'alignItems': 'center'})
    ], style={
        'display': 'flex',
        'justifyContent': 'space-between',
        'backgroundColor': COLORS['primary'],
        'padding': '20px 50px',
        'boxShadow': '0 2px 4px rgba(0,0,0,0.1)'
    }),
    html.Div([
        html.Div([
            dcc.Tabs([
                dcc.Tab(
                    label=' Report Ips ',
                    children=report_ips(),
                    className="custom-tab"
                ),
                dcc.Tab(
                    label=' Public Ip: Open ports (1000 ports) ',
                    children=report_ports(),
                    className="custom-tab"
                ),
                dcc.Tab(
                    label=' Header Report ',
                    children=report_headers(),
                    className="custom-tab"
                ),
                dcc.Tab(
                    label=' IAM: users and permissions ',
                    children=report_users(),
                    className="custom-tab"
                ),
            ], style={
                'fontFamily': 'Arial, sans-serif'
            }),
        ], className="bottom-area"),
    ], className="header-area"),
    html.Footer(
        "© 2025 By Agustina Fassina",
        style={
            'textAlign': 'center',
            'padding': '20px',
            'fontFamily': 'Arial, sans-serif',
            'color': COLORS['text_light'],
            'backgroundColor': COLORS['light'],
            'marginTop': '20px'
        }
    )
], style={'minHeight': '100vh', 'backgroundColor': COLORS['light']})

if __name__ == '__main__':
    import os
    # Compatibility with Python 3.14+
    debug_mode = os.getenv('DEBUG', 'False').lower() == 'true'
    app.run(debug=debug_mode, host='127.0.0.1', port=8050)
