from app import app
import os

import os

if __name__=="__main__":
    port = int(os.environ.get("PORT", 5229))
    app.run(host="0.0.0.0", port=port)