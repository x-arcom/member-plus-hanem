from typing import Dict


def check_health() -> Dict[str, str]:
    # TODO: add dependency checks for database, cache, and external services.
    return {
        'status': 'healthy',
        'details': 'Platform foundation is ready',
    }


def get_health_response() -> Dict[str, object]:
    health = check_health()
    return {
        'status': health['status'],
        'components': {
            'app': 'ok',
        },
        'details': health['details'],
    }
