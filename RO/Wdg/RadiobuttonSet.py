#!/usr/bin/env python

"""Creates a set of Tkinter Radiobuttons that have help, default handling
and other niceties. The set can be used in an RO.Wdg input container
(and it implements just enough of the Tkinter standard widget interface
to make this possible).

To do:
- Add contextual menu support.

History:
2003-03-26 ROwen
2003-04-15 ROwen    Modified to use RO.Wdg.CtxMenu 2003-04-15.
2003-06-12 ROwen    Fixed handling of helpText.
2003-07-10 ROwen    Added getEnable.
2003-10-16 ROwen    Mod. getEnable to return True if any button enabled.
2003-11-07 ROwen    Modified to not create a StringVar unless it'll be used.
2003-11-18 ROwen    Modified to use SeqUtil instead of MathUtil.
2003-12-05 ROwen    Added methods setDefault, set, expandValue.
                    Added abbrevOK, ignoreCase flags and changed
                    defIfDisabled to defIfBlank.
                    Added callback support.
2004-08-06 ROwen    Bug fix: was checking values against textList not valueList.
                    Bug fix: did not import RO.AddCallback.
2004-08-11 ROwen    Define __all__ to restrict import.
2004-09-14 ROwen    Bug fix: was mis-importing Radiobutton.
2004-12-13 ROwen    Renamed doEnable to setEnable for modified RO.InputCont.
2005-03-03 ROwen    Added support for bitmaps (PRELIMINARY -- UNTESTED!)
2006-03-23 ROwen    Added "side" argument to pack the widgets.
                    Added isDefault method.
                    Added support for isCurrent and autoIsCurrent.
                    Modified getWdgSet to return a copy.
2006-04-07 ROwen    Modified to allow treat a default value of None as "no default".
                    Bug fix: defIfBlank argument was ignored.
2006-05-26 ROwen    Added trackDefault argument.
                    Bug fix: added isCurrent argument to set and setDefault.
2008-04-29 ROwen    Fixed reporting of exceptions that contain unicode arguments.
2012-11-29 ROwen    Work around Aqua Tk 8.5 bug: if width specified it is too narrow
                    (the fix will need modification if this bug is also present on Aqua Tk 8.6)
                    Fixed and enhanced the demo code.
2012-11-30 ROwen    Removed __getitem__ and __len__ methods because they confuse InputCont.
                    Moved fix for Aqua Tk 8.5 width bug to RO.Wdg.Radiobutton.
2015-09-24 ROwen    Replace "== None" with "is None" to modernize the code.
2015-11-03 ROwen    Replace "!= None" with "is not None" to modernize the code.
"""
__all__ = ['RadiobuttonSet']

import tkinter
import RO.AddCallback
import RO.Alg
import RO.SeqUtil
import RO.StringUtil
import RO.TkUtil
from . import Button
from .IsCurrentMixin import AutoIsCurrentMixin, IsCurrentActiveMixin

class RadiobuttonSet (RO.AddCallback.TkVarMixin,
    AutoIsCurrentMixin, IsCurrentActiveMixin):
    """A set of Tkinter Radiobuttons with extra features.
    
    Inputs:
    - textList: a list of text labels, one per button;
                if omitted, bitmapList and valueList both must be specified
    - bitmapList: a list of bitmaps, one per button;
                if omitted, textList is used;
                if both textList and bitmapList are specified,
                the bitmap is used unless it is None
    - valueList: a list of values, one per button;
                if omitted then textList is used
    - defValue  the default value; if omitted, the first value is used
    - var       a Tkinter variable; updated when RadiobuttonSet state changes
                (and also during initialization if you specify defValue);
                if omitted, a variable is created
                if specified and the initial value is valid,
                it is used as the initial value.
    - helpText  text for hot help; may be one string (applied to all buttons)
                or a list of help strings, one per button.
    - helpURL   URL for longer help; may be one string (applied to all buttons)
                or a list of help strings, one per button.
    - callFunc  callback function; the function receives one argument: self.
                It is called whenever the value changes (manually or via
                the associated variable being set) and when setDefault is called.
    - abbrevOK  controls the behavior of set and setDefault;
                if True then unique abbreviations are allowed
    - ignoreCase controls the behavior of set and setDefault;
                if True then case is ignored
    - autoIsCurrent controls automatic isCurrent mode
        - if false (manual mode), then is/isn't current if
          set or setIsCurrent is called with isCurrent true/false
        - if true (auto mode), then is current only when all these are so:
            - set or setIsCurrent is called with isCurrent true
            - setDefValue is called with isCurrent true
            - current value == default value
    - trackDefault controls whether setDefault can modify the current value:
        - if True and isDefault() true then setDefault also changes the current value
        - if False then setDefault never changes the current value
        - if None then trackDefault = autoIsCurrent (because these normally go together)
    - defIfBlank    setDefault also sets the value if value is blank.
    - isCurrent: is the initial value current?
    - side: if "top" or "side", the widgets are packed;
        otherwise you must pack or grid them yourself.
    - any additional keyword arguments are used to configure the Radiobuttons
    """
    def __init__(self,
        master,
        textList = None,
        bitmapList = None,
        valueList = None,
        defValue = None,
        var = None,
        helpText = None,
        helpURL = None,
        callFunc=None,
        defIfBlank = True,
        abbrevOK = False,
        ignoreCase = False,
        autoIsCurrent = False,
        trackDefault = None,
        isCurrent = True,
        side = None,
    **kargs):
        self._defValue = None
        if trackDefault is None:
            trackDefault = bool(autoIsCurrent)
        self.trackDefault = trackDefault
        if textList is None and bitmapList is None:
            raise ValueError("Must specify textList or bitmapList")
        elif textList is None:
            if valueList is None:
                raise ValueError("Must specify textList or valueList")
            textList = [None]*len(bitmapList)
        else:
            # textList specified; use as default for valueList
            if valueList is None:
                valueList = textList
            
            if bitmapList is None:
                bitmapList = [None]*len(textList)
            else:
                if len(textList) != len(bitmapList):
                    raise ValueError("textList and bitmapList both specified but have different lengths")
        nButtons = len(textList)
        if len(valueList) != nButtons:
            raise ValueError("valueList must have one entry per radio button")

        self._valueList = valueList
        if var is None:
            var = tkinter.StringVar()
        self._var = var
        self._defIfBlank = defIfBlank

        self._matchItem = RO.Alg.MatchList(
            valueList = valueList,
            abbrevOK = abbrevOK,
            ignoreCase = ignoreCase,
        )
        RO.AddCallback.TkVarMixin.__init__(self, self._var)

        helpTextList = RO.SeqUtil.oneOrNAsList(helpText, nButtons, "helpText list")
        helpURLList = RO.SeqUtil.oneOrNAsList(helpURL, nButtons, "helpURL list")
        self.wdgSet = []
        for ii in range(nButtons):
            wdg = Button.Radiobutton(
                master = master,
                variable = self._var,
                text = textList[ii],
                bitmap = bitmapList[ii],
                value = valueList[ii],
                helpText = helpTextList[ii],
                helpURL = helpURLList[ii],
            **kargs)
            self.wdgSet.append(wdg)

        # do after adding callback support
        # and before setting default (which triggers a callback)
        AutoIsCurrentMixin.__init__(self, autoIsCurrent)
        IsCurrentActiveMixin.__init__(self)

        self.setDefault(defValue, isCurrent = isCurrent)
        
        if side:
            for wdg in self.wdgSet:
                wdg.pack(side=side)

        # add callback function after setting default
        # to avoid having the callback called right away
        if callFunc:
            self.addCallback(callFunc, False)
    
    def configure(self, **kargs):
        for wdg in self.wdgSet:
            wdg.configure(**kargs)

    def expandValue(self, value, doCheck=True, descr = "value"):
        """Return the value expanded (unabbreviated and with case corrected)
        and checked, as appropriate.
        
        Expansion of abbreviations and correction of case are controlled by
        ignoreCase and abbrevOK, flags supplied to __init__.
        
        Inputs:
        - value: the value to expand and check
        - doCheck: if True, raises ValueError if no match found;
            otherwise silently returns value
        - descr: description of value; typically "value" or "default".
        
        If value is None then None is always returned.
        """
        if value is None:
            return

        try:
            value = self._matchItem.getUniqueMatch(value)
        except ValueError as e:
            if doCheck:
                raise ValueError("invalid %s: %s" % (descr, RO.StringUtil.strFromException(e)))
        return value
    
    def getDefault(self):
        return self._defValue
    
    def getEnable(self):
        """Returns True if any enabled, False otherwise"""
        for wdg in self.wdgSet:
            if wdg["state"] != "disabled":
                return True
        return False

    def getVar(self):
        return self._var
    
    def getWdgSet(self):
        """Return a copy of the set of widgets.
        """
        return self.wdgSet[:]
    
    def getString(self):
        return str(self._var.get())

    def isDefault(self):
        """Return True if current value matches the default value.
        """
        return str(self._var.get()) == (self._defValue or "")
    
    def isValid(self):
        """Return True if the current value is valid"""
        return self._var.get() in self._valueList
        
    def restoreDefault(self):
        """Restore default value.
        """
        if self._defValue is None:
            return
    
        if self._defValue not in self._valueList:
            raise ValueError("invalid default %r not in %r" % (self._defValue, self._valueList))
        self._var.set(self._defValue)

    def set(self, newValue, isCurrent=True, doCheck=True, *args, **kargs):
        """Changes the currently selected radiobutton.
        
        Inputs:
        - newValue: value (not name) of button to set
        - doCheck: if True, raise an exception if value invalid,
                else accept it "as is" and have no button selected
        """
        if newValue is None:
            return
        
        newValue = self.expandValue(newValue, doCheck=doCheck, descr="button")
    
        self.setIsCurrent(isCurrent)
        self._var.set(newValue)

    def setDefault(self, newDefValue, isCurrent=None, doCheck=False, *args, **kargs):
        """Changes the default value.

        Inputs:
        - newDefValue: the new default value
        - doCheck: check that the new default value is one of the buttons

        Error conditions:
        - Raises ValueError and leaves the default unchanged
          if doCheck is True and if the new default value is invalid
        """
        newDefValue = self.expandValue(newDefValue, doCheck=doCheck, descr="default")
        restoreDef = (self.trackDefault and self.isDefault()) \
            or (self._defIfBlank and self._var.get() == "")
        self._defValue = newDefValue
        if isCurrent is not None:
            self.setIsCurrent(isCurrent)

        if restoreDef:
            self.restoreDefault()
        else:
            self._doCallbacks()

    def setEnable(self, doEnable):
        """Changes the enable state.
        """
        if doEnable:
            for wdg in self.wdgSet:
                wdg.configure(state="normal")
        else:
            for wdg in self.wdgSet:
                wdg.configure(state="disabled")
    
    def winfo_ismapped(self):
        """Needed by RO.InputCont
        """
        return self.wdgSet[0].winfo_ismapped()

if __name__ == "__main__":
    from . import PythonTk
    from .StatusBar import StatusBar
    root = PythonTk.PythonTk()

    rbFrame1 = tkinter.Frame()
    rbs1 = RadiobuttonSet(
        master = rbFrame1,
        textList = ("Foo", "Bar", "Baz"),
        valueList = ("Foo's value", "Bar's value", "Baz's value"),
        defValue = "Foo's value",
        abbrevOK = True,
        ignoreCase = True,
        autoIsCurrent = True,
        helpText = "width=0, defValue=\"Foo's value\"",
    )
    for wdg in rbs1.wdgSet:
        wdg.pack(side="left")
    rbFrame1.pack(side="top")

    rbFrame2 = tkinter.Frame()
    rbs2 = RadiobuttonSet(
        master = rbFrame2,
        textList = ("MmmmmNnnnn A", "MmmmmNnnnn B", "MmmmmNnnnn C"),
        valueList = ("A's value", "B's value", "C's value"),
        abbrevOK = True,
        ignoreCase = True,
        helpText = "width=12 (via configure)",
    )
    rbs2.configure(width = 12)
    for wdg in rbs2.wdgSet:
        wdg.pack(side="left")
    rbFrame2.pack(side="top")

    rbFrame3 = tkinter.Frame()
    rbs3 = RadiobuttonSet(
        master = rbFrame3,
        textList = ("MmmmmNnnnn A", "MmmmmNnnnn B", "MmmmmNnnnn C"),
        valueList = ("A's value", "B's value", "C's value"),
        abbrevOK = True,
        ignoreCase = True,
        indicatoron = False,
        width = 12,
        helpText = "width=12, indicatoron=False",
    )
    for wdg in rbs3.wdgSet:
        wdg.pack(side="left")
    rbFrame3.pack(side="top")
    
    def doPrint():
        print(("1 value = %r; default = %r" % (rbs1.getString(), rbs1.getDefault())))
        print(("2 value = %r; default = %r" % (rbs2.getString(), rbs2.getDefault())))
        print(("3 value = %r; default = %r" % (rbs3.getString(), rbs3.getDefault())))
    
    enableVar = tkinter.IntVar()
    enableVar.set(True)
    def setEnable():
        rbs1.setEnable(enableVar.get())
        rbs2.setEnable(enableVar.get())
        rbs3.setEnable(enableVar.get())

    StatusBar(root).pack(side="top", fill="x", expand=True)
    
    cmdFrame = tkinter.Frame()
    tkinter.Button(cmdFrame, text="Print Value", command=doPrint).pack(side="left")
    tkinter.Checkbutton(cmdFrame, text="Enable", command=setEnable, variable=enableVar).pack(side="left")
    cmdFrame.pack(side="top")

    root.mainloop()
