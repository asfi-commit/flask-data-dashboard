import os

class Config:
    """
    Central Configuration class for the flask app. 
    All reuseable settings are kept here.
    """

    #Secret key is used for session security and flash messages 
    SECRET_KEY = "your-secret-key-change-this-later"

    #Database file will be created inside the instance folder 
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    SQLALCHEMY_DATABASE_URI = "sqlite:///" + os.path.join(BASE_DIR, "instance", "users.db")

    #Disable modification tracking to save resources 
    SQLALCHEMY_TRACK_MODIFICATION = False

    #Folder to store uploaded csv files
    UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")

    #Name of the last uploaded file 
    LAST_UPLOADED_FILE = "last_uploaded.csv"