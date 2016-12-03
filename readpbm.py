#!/usr/bin/python

from math import sqrt
from math import cos
from math import sin
from math import atan

PI = 3.14159265358979323846264338327950288419716939937510582
RADIAN = PI / 180

#################################################
#                    Classes                    #
#################################################
class Image:
    def __init__(self, array, width, height, filename):
        self.pixels = array
        self.height = height
        self.width = width
        self.filename = filename

    def get(self, x, y):
        # if 0 <= x and x < self.width and 0 <= y and y < self.height:
        return self.pixels[y][x]

    def set(self, x, y, val):
        self.pixels[y][x] = val
        
    def printBox(self, x, y, width, height):
        """Print a segment of the image 'width' wide and 'height' tall starting at (x,y)"""
        for j in range(y, y+height):
            line = ""
            for i in range(x, x+width):
                if self.get(i,j) == 0:
                    line += " "
                else:
                    line += "."
            print line

    def copyBox(self, x, y, width, height):
        """Create a copy of the subset of an image"""
        resultArr = []
        for j in range(y, y+height):
            row = []
            for i in range(x, x+width):
                row.append(self.get(i,j))
            resultArr.append(row)
            
        return Image(resultArr, width, height, self.filename)
            
    def saveBox(self, x, y, width, height, filename):
        """Saves a segment of the image 'width' wide and 'height' tall starting at (x,y)"""
#        fileWidth = ((width // 8)*8) + (8 if width % 8 != 0 else 0)
#        fileHeight = ((height // 8)*8) + (8 if height % 8 != 0 else 0)
#        header = "P4\n" + str(fileWidth) + " " + str(fileHeight) + "\n"
        header = "P4\n" + str(width) + " " + str(height) + "\n"
        body = ""
        for j in range(y, y+height):
            b = 0
            count = 0
            for i in range(x, x+width):
                if self.get(i,j) != 0:
                    b = b | (1 << (7 - count))
                count += 1
                if count == 8:
                    body += chr(b)
                    b = 0
                    count = 0
            if width % 8 != 0:
                body += chr(b)
                    
        with open(filename, "w") as fout:
            fout.write(header)
            fout.write(body)
            fout.close()

    def saveCopy(self, filename):
        self.saveBox(0,0, self.width, self.height, filename)
            
    def save(self):
        self.saveCopy(self.filename)
            
    def copy(self):
        return self.copyBox(0, 0, self.width, self.height)
            
    def findSeamAndSplit(self):
        startArr = []
        endArr = []
        
        #go row by row and find the likely start and end for each seam, add to arrays
        for j in range(0, self.height):
            startX, endX = self.findSeamRange(j)
            if startX != -1 and endX != -1:
                startArr.append((startX, j))
                endArr.append((endX, j))
                
        #find the best linear approximation for left side of the seam and crop
        m, b = fitLineToPoints(startArr)
        cropEnd = self.width - 1
        for x in range(0, self.width):
            y = int(m * x + b)
            if 0 <= y and y < self.height:
                cropEnd = min(cropEnd, x)
        leftPage = self.copyBox(0, 0, cropEnd + 1, self.height)
        leftPage.filename = self.filename[0:self.filename.rfind(".")] + "l" + self.filename[self.filename.rfind("."):]
        
        #find the best linear approximation for the right side and crop
        m, b = fitLineToPoints(endArr)
        cropStart = 0
        for x in range(0, self.width):
            y = int(m * x + b)
            if 0 <= y and y < self.height:
                cropStart = max(cropStart, x)
        rightPage = self.copyBox(cropStart, 0, self.width - cropStart - 1, self.height)
        rightPage.filename = self.filename[0:self.filename.rfind(".")] + "r" + self.filename[self.filename.rfind("."):]
        
        return leftPage, rightPage
        
    def findSeamRange(self, rowNum):
        """Returns a tuple with the range of x values where we think the seam is - may be -1 if can't find"""
        #case 1, seam is in direct middle of image
        #case 2, seam to left of direct middle
        #case 3, seam to right of direct middle
        startX = self.width // 2
        result = None
        
        #case 1:
        if self.get(startX, rowNum) == 1:
            #just look left and right until you find a white pixel on both ends, store in tuple
            leftShift = 0
            rightShift = 0
            while self.get(startX + leftShift, rowNum) != 0 or self.get(startX + rightShift, rowNum) != 0:
                if self.get(startX + leftShift, rowNum) != 0:
                    leftShift -= 1
                if self.get(startX + rightShift, rowNum) != 0:
                    rightShift += 1
                if startX + rightShift >= self.width  or startX + leftShift < 0:
                    # leftShift = -1 * (startX + 1)
                    # rightShift = -1 * (startX + 1)
                    return (-1,-1)
            result = (startX + leftShift + 1, startX + rightShift - 1)
        
        #cases 2 & 3:
        else:
            #look left and right until you find a black pixel
            leftShift = 0
            rightShift = 0
            while self.get(startX + leftShift, rowNum) != 1 and self.get(startX + rightShift, rowNum) != 1:
                if self.get(startX + leftShift, rowNum) != 1:
                    leftShift -= 1
                if self.get(startX + rightShift, rowNum) != 1:
                    rightShift += 1
                if startX + rightShift >= self.width  or startX + leftShift < 0:
                    return (-1,-1)
                
            #case 2:
            if self.get(startX + leftShift, rowNum) == 1:
                #look left until you find the end of this row
                moreLeftShift = 0
                while self.get(startX + leftShift + moreLeftShift, rowNum) != 0:
                    moreLeftShift -= 1
                    if startX + leftShift + moreLeftShift == 0:
                        break
                result = (startX + leftShift + moreLeftShift + 1, startX + leftShift)
                
            #case 3:
            else:
                #look right until you find the end of this row
                moreRightShift = 0
                while self.get(startX + rightShift + moreRightShift, rowNum) != 0:
                    moreRightShift += 1
                    if startX + rightShift + moreRightShift == self.width - 1:
                        break
                result = (startX + rightShift, startX + rightShift + moreRightShift - 1)
                
        return result

    def clearMargins(self, width):
        """clears all pixels within 'width' of an edge"""
        for x in range(0, width):
            for y in range(0, self.height):
                self.set(x,y,0)
        for x in range(self.width-width-1, self.width):
            for y in range(0, self.height):
                self.set(x,y,0)
        for y in range(0, width):
            for x in range(0, self.width):
                self.set(x,y,0)
        for y in range(self.height-width-1, self.height):
            for x in range(0, self.width):
                self.set(x,y,0)
    
    def findMarginFromLeft(self):
        #find all the left edges
        edgePoints = []
        for y in range(0, self.height):
            for x in range(0, self.width//4):
                if self.get(x, y) == 1:
                    edgePoints.append((x, y))
                    break
        
        #remove points not within a reasonable std dev of average and fit a line
        m, b = fitLineToPoints(removeOutliersX(edgePoints))
        return (m,b)
        
    def graphLine(self, m, b):
        """Graph the line with the given slope and y-intercept
        Assumes that the slope is at least 1, otherwise should reverse from
        filling in the y-direction to filling in the x-direction"""
        
        #find points lying in the image
        graphPoints = []
        for x in range(0, self.width):
            y = int(m * x + b)
            if 0 <= y and y < self.height:
                graphPoints.append((x,y))
        
        #graph segments filling in the line
        for i in range(0, len(graphPoints) - 1):
            currX, currY = graphPoints[i]
            nextX, nextY = graphPoints[i+1]
            for y in range(min(currY, nextY), max(currY, nextY)):
                self.set(currX-1, y, 0)
                self.set(currX, y, 1)
                self.set(currX+1, y, 0)
    
    def bloat(self, numTimes):
        for nt in range(0, numTimes):
            newPixels = [list(row) for row in self.pixels]
            for y in range(0, self.height):
                for x in range(0, self.width):
                    if self.get(x,y) == 1:
                        for j in range(max(y-1,0), min(y+2,self.height)):
                            for i in range(max(x-1,0), min(x+2,self.width)):
                                newPixels[j][i] = 1
            self.pixels = newPixels
    
    def rotate(self, radians):
        #complex analysis saves the day:
        # rotate x+i*y about cx+i*cy by theta radians?
        #(((x-cx)+i(y-cy))*(cos(theta)+i*sin(theta))) + cx+i*cy
        # = ((x-cx)*cos(theta)-(y-cy)*sin(theta)+cx) + i((x-cx)*sin(theta)+(y-cy)*cos(theta)+cy)
        centerX = self.width // 2
        centerY = self.height // 2
        newPixels = []
        for y in range(0, self.height):
            row = []
            for x in range(0, self.width):
                srcX = (x-centerX)*cos(-1*radians) - (y-centerY)*sin(-1*radians) + centerX
                srcY = (x-centerX)*sin(-1*radians) + (y-centerY)*cos(-1*radians) + centerY
                
                if 0 <= srcX and srcX < self.width-1 and 0 <= srcY and srcY < self.height-1:
                    # row.append(self.get(int(srcX), int(srcY)))
                    row.append(self.sampleAroundPoint(srcX, srcY))
                else:
                    row.append(0)
            newPixels.append(row)
        self.pixels = newPixels
        
    def sampleAroundPoint(self, x ,y):
        """return a weighted average, rounded in the more usual way, of the 4 pixels about
        the given point.  The point is the rotation of another pixel, and for simplicity
        we assume translation over having to compute areas of triangles and junk"""
        #grazi:
        #http://www.leptonica.com/rotation.html
        xDec = x % 1
        yDec = y % 1
        weightUL = self.get(int(x), int(y)) * (1-xDec) * (1-yDec)
        weightUR = self.get(int(x)+1, int(y)) * xDec * (1-yDec)
        weightLL = self.get(int(x), int(y)+1) * (1-xDec) * yDec
        weightLR = self.get(int(x)+1, int(y)+1) * xDec * yDec
        return round(weightUL + weightUR + weightLL + weightLR)
    
    def determineRotationAngle(self, m, b):
        """Assuming that we rotate about the center, find the angle of rotation in radians"""
        #find first and last x,y pairs that are on the line and in the image - for triangle
        pair1 = None
        for x in range(0, self.width):
            y = m * x + b
            if 0 <= y and y < self.height:
                pair1 = (float(x),y)
                break
        pair2 = None
        for x in range(self.width-1, -1, -1):
            y = m * x + b
            if 0 <= y and y < self.height:
                pair2 = (float(x),y)
                break
        
        #find the angle with arctan
        angle = atan(abs(pair1[0] - pair2[0]) / abs(pair1[1] - pair2[1]))
        if m < 0:
            angle = -1 * angle
        return angle
    
    
#################################################
#                    Methods                    #
#################################################
def isWhitespace(char):
    """Check if the given character is a whitespace character.  There's probably a more pythonic way to do this."""
    if char == " " or char == "\t" or char == "\n" or char == "\r" or char == "\v" or char == "\f":
        return True
    else:
        return False

def skipWhitespace(fReading, currC=" "):
    """Given an opened file, and possibly a current character, read until something isn't a whitespace character and return."""
    c = currC
    while c != "" and isWhitespace(c):
        c = fReading.read(1)
    return c

def readInArray(filename):
    with open(filename, "rb") as fin:
        try:
            #check the P4 header
            c = skipWhitespace(fin)
            text = ""
            while c != "" and not isWhitespace(c):
                text += c
                c = fin.read(1)
            #print "|" + text + "|"
            if text != "P4":
                print "Wrong kind of file, invalid header"
                exit(1)

            #get the width
            c = skipWhitespace(fin, c)
            text = ""
            while c != "" and not isWhitespace(c):
                text += c
                c = fin.read(1)
            #print "|" + text + "|"
            width = int(text)

            #get the height
            c = skipWhitespace(fin, c)
            text = ""
            while c != "" and not isWhitespace(c):
                text += c
                c = fin.read(1)
            #print "|" + text + "|"
            height = int(text)

            #there is only one final whitespace character after the header,
            #which at this point is stored in c, so we now start consuming
            #the binary bitmap
            numBytesRow = width // 8
            if width % 8 != 0:
                numBytesRow += 1
            rows = []
            for i in range(0, height):
                rows.append(fin.read(numBytesRow))
        finally:
            fin.close()

    #take the strings and extract the bits into integer arrays (wasteful)
    #may require fiddling with bit stuff for endianness later
    resultArr = []
    for i in range(0, height):
        rowArr = []
        for j in range(0, len(rows[i])):
            byte = ord(rows[i][j])
            for k in range(0,8):
                rowArr.append((byte >> (7-k)) & 1)
        resultArr.append(rowArr)
    result = Image(resultArr, width, height, filename)
    return result
        
def fitLineToPoints(points):
    """returns (m, b) for line y=mx+b that best fits the given array of (x,y) tuples
    Stoled from:
    http://www.varsitytutors.com/hotmath/hotmath_help/topics/line-of-best-fit
    """
    
    #compute averages
    xAvg = 0.0
    yAvg = 0.0
    for n in range(1, len(points)+1):
        xAvg = (xAvg * (n-1) / n) + (float(points[n-1][0]) / n)
        yAvg = (yAvg * (n-1) / n) + (float(points[n-1][1]) / n)
        
    #compute slope
    sumNum = 0
    sumDen = 0
    for n in range(0, len(points)):
        sumNum += (points[n][0] - xAvg) * (points[n][1] - yAvg)
        sumDen += (points[n][0] - xAvg) ** 2
        
    #return
    m = sumNum / sumDen
    b = yAvg - m * xAvg
    return (m, b)
    
def removeOutliersX(points):
    #compute stats, stoled from:
    #http://codeselfstudy.com/blogs/how-to-calculate-standard-deviation-in-python
    nums = [p[0] for p in points]
    mean = float(sum(nums))/len(nums)
    differences = [n - mean for n in nums]
    sq_differences = [d ** 2 for d in differences]
    ssd = sum(sq_differences)
    stdDev = sqrt(ssd / len(nums))
    
    #only return points within half a std dev
    result = []
    for p in points:
        if mean - (stdDev/4) <= p[0] and p[0] <= mean + (stdDev/4):
            result.append(p)
    return result

def round(decimal):
    if decimal % 1 >= 0.5:
        return int(decimal) + 1
    else:
        return int(decimal)
    
    
#################################################
#                Script Start                   #
#################################################

image = readInArray("upnt-003.pbm")
#printBox(image, 0,0,79,100)
#image.saveBox(0,0,1,1, "test.pbm")
# image.saveBox(0,0,79,100, "test.pbm")
image.filename = "seam3.pbm"
leftPage, rightPage = image.findSeamAndSplit()
leftPage.save()
rightPage.clearMargins(10)
bloatedRight = rightPage.copy()
bloatedRight.bloat(7)
m, b = bloatedRight.findMarginFromLeft()
# rightPage.graphLine(m, b)
angle = rightPage.determineRotationAngle(m, b)
rightPage.rotate(angle)
rightPage.save()


#pizza - probably smarter for line of best fit to find the equation for x in terms of y
#to avoid arbitrarily large slopes when the page doesn't need to be rotated
#plus we can check if the slope is within epsilon of 0, in which case, don't bother rotating