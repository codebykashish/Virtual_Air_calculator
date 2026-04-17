import cv2
import mediapipe as mp
from cvzone.HandTrackingModule import HandDetector

class Button:
    def __init__(self, text, width=70, height=70):
        self.text = text
        self.width = width
        self.height = height
        self.pos = [0, 0]

    def draw(self, img, x, y, isHover=False, isPressed=False):
        self.pos = [x, y]
        # Haptic Visual: Shrink when pressed
        offset = 6 if isPressed else 0
        
        imgNew = img.copy()
        # COLOR LOGIC: Green for click, Purple for hover, Grey/Red for default
        if isPressed: color = (0, 255, 0) # GREEN CLICK
        elif isHover: color = (255, 0, 255) # PURPLE HOVER
        elif self.text == "C": color = (200, 200, 255) # REDDISH CLEAR
        else: color = (225, 225, 225) # DEFAULT

        cv2.rectangle(imgNew, (x + offset, y + offset), 
                      (x + self.width - offset, y + self.height - offset), 
                      color, cv2.FILLED)
        cv2.rectangle(img, (x + offset, y + offset), 
                      (x + self.width - offset, y + self.height - offset), 
                      (50, 50, 50), 2)
        
        alpha = 0.4
        cv2.addWeighted(imgNew, alpha, img, 1 - alpha, 0, img)
        cv2.putText(img, self.text, (x + 20, y + 45), 
                    cv2.FONT_HERSHEY_PLAIN, 2, (50, 50, 50), 2)

# --- INITIALIZATION ---
buttonValues = [['C', '<', '/', '*'],
                ['7', '8', '9', '-'],
                ['4', '5', '6', '+'],
                ['1', '2', '3', '='],
                ['0', '.', '', '']]

myButtons = []
for row in buttonValues:
    tempRow = []
    for char in row:
        tempRow.append(Button(char) if char != '' else None)
    myButtons.append(tempRow)

cap = cv2.VideoCapture(0)
cap.set(3, 1280); cap.set(4, 720)
detector = HandDetector(detectionCon=0.8, maxHands=1)

# STATE VARIABLES
myEquation = ""
delayCounter = 0
resultsDisplayed = False
isDynamic = True # Starts in 'Follow' mode
stablePos = [800, 150] # Default stable position

while True:
    success, img = cap.read()
    if not success: break
    img = cv2.flip(img, 1)
    hands, img = detector.findHands(img, flipType=False)

    # 1. KEYBOARD TOGGLES
    key = cv2.waitKey(1) & 0xFF
    if key == ord('s'): isDynamic = False # FREEZE
    if key == ord('f'): isDynamic = True  # FOLLOW
    if key == ord('q'): break

    if hands:
        lmList = hands[0]["lmList"]
        cursorX, cursorY = lmList[8][0], lmList[8][1]
        length, _, img = detector.findDistance(lmList[8][0:2], lmList[12][0:2], img)
        
        # 2. POSITION LOGIC
        if isDynamic:
            anchorX, anchorY = lmList[0][0], lmList[0][1]
            # Save the current position in case we hit 's'
            stablePos = [anchorX - 140, anchorY - 400] 
        
        # 3. DRAW & INTERACT
        for r, row in enumerate(myButtons):
            for c, button in enumerate(row):
                if button:
                    bx = stablePos[0] + (c * 80)
                    by = stablePos[1] + (r * 80)
                    
                    isHover = bx < cursorX < bx + button.width and by < cursorY < by + button.height
                    isPressed = isHover and length < 40

                    button.draw(img, bx, by, isHover, isPressed)

                    if isPressed and delayCounter == 0:
                        if button.text == "=":
                            try: myEquation = str(eval(myEquation))
                            except: myEquation = "Error"
                            resultsDisplayed = True
                        elif button.text == "C":
                            myEquation = ""; resultsDisplayed = False
                        elif button.text == "<":
                            myEquation = myEquation[:-1]
                        else:
                            if resultsDisplayed:
                                myEquation = button.text if button.text not in "+-*/" else myEquation + button.text
                                resultsDisplayed = False
                            else:
                                myEquation += button.text
                        delayCounter = 1

    # Logic & Display
    if delayCounter != 0:
        delayCounter += 1
        if delayCounter > 10: delayCounter = 0

    # Display Results & Mode Indicator
    modeText = "FOLLOW MODE (F)" if isDynamic else "STABLE MODE (S)"
    cv2.putText(img, modeText, (50, 40), cv2.FONT_HERSHEY_PLAIN, 2, (255, 0, 0), 2)
    cv2.rectangle(img, (50, 60), (450, 130), (255, 255, 255), cv2.FILLED)
    cv2.putText(img, myEquation, (60, 110), cv2.FONT_HERSHEY_PLAIN, 3, (0, 0, 0), 3)

    cv2.imshow("Hybrid HUD Calculator", img)

cap.release()
cv2.destroyAllWindows()