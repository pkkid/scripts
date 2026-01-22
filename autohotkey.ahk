; My Custom Shortcuts
; https://www.autohotkey.com/docs/v2/lib/
; https://documentation.help/AutoHotkey-en/Hotkeys.htm#Symbols
;
; Modifier symbols:
;   #  Win, ! Alt, ^ Ctrl, + Shift
;   &  Combine hotkeys (ex. ^!a & ^!b)
;   >  Use the right key of the pair (ex. >!a)
;   <  Use the left key of the pair (ex. <!a)
;   ~  Dont block keys native function (ex. ~LButton)
;   *  Wildcard: Fire even if extra modifiers held down
;   UP  Cause hotkey to fire upon release (ex. F1 & e Up::)
#SingleInstance

; Win: Open Flow Launcher while still retaining regular Win+Key shortcuts
; https://github.com/Flow-Launcher/Flow.Launcher/discussions/747#discussioncomment-8336756
; ~LWin::Send "{Blind}{VKFF}"   ; Prevent Start Menu from showing if pressed by itself
; LWin Up::{
;   if (A_PriorKey = "LWin") {  ; Check Lwin down then up without other keys in between
;     Send "^{Space}"           ; Ctrl+Space
;   }
; }


; Alt+`: Open a new PS terminal
; Win+`: Open a new WSL terminal
!`:: {
  Run "wt new-tab"
}
#`::{
  Run "wt new-tab --profile `"Ubuntu-24.04`""
}


; Win+P: Lock screen and put monitors to sleep 
; https://www.autohotkey.com/docs/v2/lib/SendMessage.htm#Examples
; 0x0112 is WM_SYSCOMMAND, 0xF170 is SC_MONITORPOWER.
#p::{
  DllCall("LockWorkStation")
  Sleep 1500  ; Give user a chance to release keys
  SendMessage 0x0112, 0xF170, 2,, "Program Manager" 
}


