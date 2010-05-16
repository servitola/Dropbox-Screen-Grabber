import os
import sys
import datetime

import Image
import ImageGrab
import win32gui
import win32clipboard
import win32ui
import win32con

import settings

# Dropbox database files (0.7 uses dropbox.db and 0.8 uses config.db)
DROPBOX_DATABASE_FILES = ('dropbox.db', 'config.db')

def get_dropbox_path():
    '''
    Retrieve the Dropbox path.
    
    Keyword arguments:
    none

    Returns: string
    '''
    
    import ctypes, base64, pickle, sqlite3, os
    is_windows = True
    
    try:
        # try to get Windows path first
        SHGetFolderPath = ctypes.windll.shell32.SHGetFolderPathW
    except AttributeError:
        is_windows = False
    
    if is_windows:
        from ctypes.wintypes import HWND, HANDLE, DWORD, LPCWSTR, MAX_PATH
        SHGetFolderPath.argtypes = [HWND, ctypes.c_int, HANDLE, DWORD, LPCWSTR]
        path_buffer = ctypes.wintypes.create_unicode_buffer(MAX_PATH)
        
        # 26 is CSIDL_APPDATA, the code for retrieving the user's Application Data folder
        SHGetFolderPath(0, 26, 0, 0, path_buffer)

        dropbox_db_path = None
        for file in DROPBOX_DATABASE_FILES:
            path = os.path.join(path_buffer.value, 'Dropbox', file)

            if os.path.exists(path):
	            dropbox_db_path = path
	            break
    else:
        dropbox_db_path = os.path.expanduser('~/.dropbox/dropbox.db')
    
    if not dropbox_db_path:
	    raise IOError('Dropbox database file not found')

    try:    
        db = sqlite3.connect(dropbox_db_path)
        cur = db.cursor()
        cur.execute("select key, value from config where key = 'dropbox_path'")
        row = cur.fetchone()

        if row:
	        try:
	            return pickle.loads(base64.b64decode(row[1]))
	        except Exception, e:
	            # Most likely a 0.8 branch where values are not base64 encoded and pickled
		        return row[1]

        # No dropbox_path key found, assume that the folder is located in the default location
        dropbox_path = os.path.join(os.path.expanduser('~'), 'My Documents', 'My Dropbox')

        if not os.path.exists(dropbox_path):
	        raise IOError('Could not find Dropbox folder')

        return dropbox_path
    except Exception, e:
        raise IOError('Problems reading the Dropbox database')

def get_current_active_window_placement():
    '''
    Return coordinates of the currently active window.
    
    Keyword arguments:
    none

    Returns: tuple with 4 coordinates (left, upper, right, lower)
    '''
    
    flags, showcmd, (xy, yx), (minposX, minposY), (maxposX, maxposY, normalposX, normalposY) = win32gui.GetWindowPlacement(win32gui.GetForegroundWindow())
    
    return (maxposX, maxposY, normalposX, normalposY)

def grab_screenshot(fullScreen = 'true', copyUrlIntoClipboard = 'false', userId = ''):
    '''
    Grab a screenshot.
    
    Keyword arguments:
    string fullScreen -- true to capture the full screen, false to capture only the currently active window
    string copyUrlToClipboard -- true to copy the public URL to the clipboard

    Returns: none
    '''
    
    if fullScreen == 'true':
        image = ImageGrab.grab()
    else:
        image = ImageGrab.grab(get_current_active_window_placement())
     
    time = datetime.datetime.now().strftime("%Y%m%d%H%M%S"); 
    fileName = 'screengrab_' + time + '.png'
    
    settings.loadSettings()   
    saveFolderPath = os.path.join(publicFolderPath, settings.settings['screenshotSaveDirectory'])
    saveLocation = os.path.join(saveFolderPath, fileName)  
    
    # Save a screenshot to the Dropbox public folder and (optionaly) copy the file url into the clipboard
    image.save(saveLocation, 'PNG')
    
    if copyUrlIntoClipboard == 'true' and userId != '':
        copy_url_to_clipboard(userId, fileName)
        
    return fileName
       
def copy_url_to_clipboard(userId, fileName):
    '''
    Copy a public link of the saved screenshot to the clipboard.
    
    Keyword arguments:
    fileName -- Screnshot filename

    Returns: none
    '''
	
    if settings.settings['screenshotSaveDirectory'] != '':
		saveDirectory = settings.settings['screenshotSaveDirectory'].replace('\\', '/')
		saveDirectory = saveDirectory.replace(' ', '%20')
		publicURL = 'http://dl.getdropbox.com/u/%s/%s/%s' % (userId, saveDirectory, fileName)
    else:
		publicURL = 'http://dl.getdropbox.com/u/%s/%s' % (userId, fileName)

    win32clipboard.OpenClipboard()
    win32clipboard.EmptyClipboard()
    win32clipboard.SetClipboardText(publicURL)
    win32clipboard.CloseClipboard()
    
publicFolderPath = os.path.join(get_dropbox_path(), 'Public')