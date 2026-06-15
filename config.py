import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    
    # Retrieve and clean database URL
    db_url = os.environ.get('DATABASE_URL')
    if not db_url:
        # Fallback to shared SQLite in sad-central-mcdm/instance/mcdm_central.db if running from a sibling directory
        base_dir = os.path.abspath(os.path.dirname(__file__))
        parent_dir = os.path.dirname(base_dir)
        central_db_path = os.path.join(parent_dir, 'sad-central-mcdm', 'instance', 'mcdm_central.db')
        
        # Check if the folder of the central database exists (even if running from central itself or sibling)
        if os.path.exists(os.path.dirname(central_db_path)):
            db_url = f"sqlite:///{central_db_path.replace(os.sep, '/')}"
        else:
            db_url = 'sqlite:///mcdm_central.db'
            
    if db_url.startswith('postgres://'):
        db_url = db_url.replace('postgres://', 'postgresql://', 1)
        
    SQLALCHEMY_DATABASE_URI = db_url
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Session configurations
    SESSION_TYPE = 'filesystem'
    
    # System Mode config: 'central', 'smarts_smarter', 'ahp', 'bwm', 'macbeth', 'bwt'
    SYSTEM_MODE = os.environ.get('SYSTEM_MODE', 'central')
    
    # Mapping for Titles
    SYSTEM_TITLE_MAP = {
        'central': 'NEXUS MCDM',
        'smarts_smarter': 'Nexus SMARTS/SMARTER',
        'ahp': 'Nexus AHP',
        'bwm': 'Nexus BWM',
        'macbeth': 'Nexus MACBETH',
        'bwt': 'Nexus BWT',
        'topsis': 'Nexus TOPSIS',
        'vikor': 'Nexus VIKOR',
        'electre': 'Nexus ELECTRE',
        'promethee': 'Nexus PROMETHEE'
    }
    
    SYSTEM_TITLE = SYSTEM_TITLE_MAP.get(SYSTEM_MODE, 'NEXUS MCDM')

