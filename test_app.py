from flask import Flask

app = Flask(__name__)

@app.route('/')
def hello():
    return '''
    <h1>Test App Çalışıyor!</h1>
    <p>Bu basit Flask uygulaması çalışıyor demektir.</p>
    <p>Ana app.py dosyasında import problemi var.</p>
    '''

@app.route('/test_imports')
def test_imports():
    try:
        # Test basic imports
        import os
        import json
        from datetime import datetime
        from dotenv import load_dotenv
        
        # Load environment
        load_dotenv()
        
        results = {
            'basic_imports': 'OK',
            'dotenv': 'OK',
            'env_vars': {
                'GOOGLE_API_KEY': 'SET' if os.environ.get('GOOGLE_API_KEY') else 'MISSING',
                'TWITTER_BEARER_TOKEN': 'SET' if os.environ.get('TWITTER_BEARER_TOKEN') else 'MISSING'
            }
        }
        
        # Test utils import
        try:
            from utils import load_json
            results['utils_basic'] = 'OK'
        except Exception as e:
            results['utils_basic'] = f'ERROR: {str(e)}'
            
        # Test safe_log import
        try:
            from utils import safe_log
            results['safe_log'] = 'OK'
        except Exception as e:
            results['safe_log'] = f'ERROR: {str(e)}'
            
        return f'<pre>{json.dumps(results, indent=2)}</pre>'
        
    except Exception as e:
        return f'<h2>Import Test Failed:</h2><p>{str(e)}</p>'

if __name__ == '__main__':
    app.run(debug=True)