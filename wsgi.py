from AlgoLaw_Website import app
import os

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(port=port, debug=True, threaded=True)
# app.run()
