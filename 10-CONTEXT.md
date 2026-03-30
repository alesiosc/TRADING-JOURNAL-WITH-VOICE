
========================================
  Trading Journal Pro
========================================

Starting application...

Traceback (most recent call last):
  File "D:\MyPythonProjects_2\TRADING JOURNAL WITH VOICE\trading_journal_final.py", line 779, in <module>
    app = TradingJournalFinal(root)
  File "D:\MyPythonProjects_2\TRADING JOURNAL WITH VOICE\trading_journal_final.py", line 243, in __init__
    tk.Button(control_frame, text="Define Crop", command=self.define_crop_region, font=("Arial", 9, "bold"), bg="#000000", fg="white", padx=10).grid(row=0, column=6, padx=10)
                                                         ^^^^^^^^^^^^^^^^^^^^^^^
AttributeError: 'TradingJournalFinal' object has no attribute 'define_crop_region'. Did you mean: 'clear_crop_region'?

ERROR: Failed to start application

Press any key to continue . . .