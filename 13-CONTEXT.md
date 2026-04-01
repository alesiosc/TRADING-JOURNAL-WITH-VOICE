2. Initializing STT module...
Traceback (most recent call last):
  File "D:\MyPythonProjects_2\TRADING JOURNAL WITH VOICE\test_stt.py", line 41, in <module>
    main()
    ~~~~^^
  File "D:\MyPythonProjects_2\TRADING JOURNAL WITH VOICE\test_stt.py", line 19, in main
    stt = create_stt_module("stt_module/config.yaml")
  File "D:\MyPythonProjects_2\TRADING JOURNAL WITH VOICE\stt_module\__init__.py", line 84, in create_stt_module
    return STTModule(config_path)
  File "D:\MyPythonProjects_2\TRADING JOURNAL WITH VOICE\stt_module\__init__.py", line 19, in __init__
    with open(config_full_path, 'r') as f:
         ~~~~^^^^^^^^^^^^^^^^^^^^^^^
FileNotFoundError: [Errno 2] No such file or directory: 'D:\\MyPythonProjects_2\\TRADING JOURNAL WITH VOICE\\stt_module\\stt_module/config.yaml'
 Python 3.13.3 PS D:\MyPythonProjects_2\TRADING JOURNAL WITH VOICE>  