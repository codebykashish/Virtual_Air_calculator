import cv2
import mediapipe as mp
import sys
from cvzone.HandTrackingModule import HandDetector

# --- 1. THE BUTTON CLASS ---
class Button:
    def __init__(self, pos, text, width=80, height=80):
        self.pos = pos
        self.text = text
        self.width = width
        self.height = height

    def draw(self, img):
        imgNew = img.copy()
        # Reddish for Clear, Greenish for Equal, Grey for others
        if self.text == "C": color = (200, 200, 255)
        elif self.text == "=": color = (200, 255, 200)
        else: color = (225, 225, 225)
        
        cv2.rectangle(imgNew, self.pos, (self.pos[0] + self.width, self.pos[1] + self.height), 
                      color, cv2.FILLED)
        cv2.rectangle(imgNew, self.pos, (self.pos[0] + self.width, self.pos[1] + self.height), 
                      (50, 50, 50), 3)
        
        alpha = 0.3
        cv2.addWeighted(imgNew, alpha, img, 1 - alpha, 0, img)
        cv2.putText(img, self.text, (self.pos[0] + 25, self.pos[1] + 60), 
                    cv2.FONT_HERSHEY_PLAIN, 2, (50, 50, 50), 2)

# --- 2. INITIALIZE BUTTONS ---
buttonListValues = [['C', '<', '/', '*'],
                    ['7', '8', '9', '-'],
                    ['4', '5', '6', '+'],
                    ['1', '2', '3', '='],
                    ['0', '.', '', '']]

buttonList = []
for x in range(4):
    for y in range(5):
        xpos = x * 100 + 800
        ypos = y * 100 + 150
        if buttonListValues[y][x] != '':
            buttonList.append(Button((xpos, ypos), buttonListValues[y][x]))

# --- 3. SYSTEM SETUP ---
cap = cv2.VideoCapture(0)
cap.set(3, 1280)
cap.set(4, 720)
detector = HandDetector(detectionCon=0.8, maxHands=1)

# Variables for State Management
delayCounter = 0
myEquation = ""
resultsDisplayed = False 

while True:
    success, img = cap.read()
    if not success: break
    img = cv2.flip(img, 1)

    # A. Hand Tracking (On clean image)
    hands, img = detector.findHands(img, flipType=False)

    # B. Draw HUD Screen
    cv2.rectangle(img, (800, 50), (1180, 130), (225, 225, 225), cv2.FILLED)
    cv2.rectangle(img, (800, 50), (1180, 130), (50, 50, 50), 3)
    
    # C. Draw Buttons
    for button in buttonList:
        button.draw(img)

    # D. Logic for Interaction
    if hands:
        lmList = hands[0]["lmList"]
        p1 = lmList[8][0:2] # Index
        p2 = lmList[12][0:2] # Middle
        length, info, img = detector.findDistance(p1, p2, img)
        x, y = lmList[8][0], lmList[8][1]

        for button in buttonList:
            bx, by = button.pos
            bw, bh = button.width, button.height

            if bx < x < bx + bw and by < y < by + bh:
                # Hover Effect
                cv2.rectangle(img, (bx-5, by-5), (bx + bw + 5, by + bh + 5), (255, 0, 255), cv2.FILLED)
                cv2.putText(img, button.text, (bx + 25, by + 60), cv2.FONT_HERSHEY_PLAIN, 2, (255, 255, 255), 4)

                # CLICK LOGIC
                if length < 40 and delayCounter == 0:
                    cv2.rectangle(img, button.pos, (bx + bw, by + bh), (0, 255, 0), cv2.FILLED)
                    
                    # 1. Handle Calculation
                    if button.text == "=":
                        try:
                            myEquation = str(eval(myEquation))
                        except:
                            myEquation = "Error"
                        resultsDisplayed = True
                    
                    # 2. Handle Clear
                    elif button.text == "C":
                        myEquation = ""
                        resultsDisplayed = False
                    
                    # 3. Handle Backspace
                    elif button.text == "<":
                        myEquation = myEquation[:-1]
                    
                    # 4. Handle Numbers and Operators
                    else:
                        if resultsDisplayed:
                            if button.text in "+-*/":
                                resultsDisplayed = False # Continue calculating with answer
                                myEquation += button.text
                            else:
                                myEquation = button.text # Start fresh number
                                resultsDisplayed = False
                        else:
                            # Prevent double operators
                            if len(myEquation) > 0 and button.text in '+-*/' and myEquation[-1] in '+-*/':
                                pass 
                            else:
                                myEquation += button.text
                    
                    delayCounter = 1 # Start Cooldown

    # E. Cooldown Timer (Debounce)
    if delayCounter != 0:
        delayCounter += 1
        if delayCounter > 10: # Wait 10 frames
            delayCounter = 0

    # F. Display Final Text
    cv2.putText(img, myEquation, (810, 110), cv2.FONT_HERSHEY_PLAIN, 3, (50, 50, 50), 3)

    cv2.imshow("Air Calculator - Final Version", img)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
