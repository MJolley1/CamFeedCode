# Import some frameworks
import os
import os.path
import datetime as dt
import time
from time import sleep
import threading
import shutil
import RPi.GPIO as GPIO
import subprocess
import shlex
from threading import Timer
from datetime import datetime, timedelta
from glob import glob
from distutils.dir_util import copy_tree
import io
import serial
import sys


# Run the c++ program which checks for connectivity and waits if there is no internet connection is available
# subprocess.Popen("sudo /home/pi/cooking/arduPi/MY_PROGRAM",shell=True).wait # os.system("sudo /home/pi/cooking/arduPi/MY_PROGRAM")

# Make the program sleep for 10 seconds to allow for connectivity through wvdial if modem is powered up
time.sleep(10)

# Clean-up the data folder
if os.path.exists('/home/pi/Data/'):
    subFolder = [d for d in os.listdir('/home/pi/Data/') if os.path.isdir(os.path.join('/home/pi/Data/', d))] # list the subfolders (only)
    if len(subFolder) > 0:
        try:
            os.remove ('/home/pi/Data/pingresult.txt')
            os.remove ('/home/pi/Data/UltrasonicOutput.txt')
            os.remove ('/home/pi/Data/VoltageReadings.txt')
        except OSError:
            pass
        for root, dirs, files in os.walk('/home/pi/Data'):
            for file in files:
                path_file = os.path.join(root,file)
                shutil.copy2(path_file,'/home/pi/backupData')
        shutil.rmtree('/home/pi/Data/') # This removes all files and subfolders
        os.makedirs('/home/pi/Data/', mode=0777) # Make the Data folder
else:
    os.makedirs('/home/pi/Data/', mode=0777) # Make the Data folder

zz = 15 # Number of minutes between video/photo interval
#counter = 0 # Counter for the upload section

# Define the site location identifier
siteName = "z_millbrook" # This needs to be all lower-case for compatability with AWS

# Define the IP cameras IP address and the RTSP port
camAddress = "169.254.240.100:554" # default IP address
#camAddress = "192.168.2.202" # Grizedale-ph IP address

# Grab the initial datetime information
d = datetime.now()
initYear = "%04d" % (d.year) 
initMonth = "%02d" % (d.month) 
initDate = "%02d" % (d.day)
initHour = "%02d" % (d.hour)
initMins = "%02d" % (d.minute)
initSecs = "%02d" % (d.second)

# Define the location where you wish to save files & Create a new bucket on the AWS server
condition = 1
while condition == 1:
    folderToSave = siteName + "-" + str(initYear) + str(initMonth) + str(initDate) + str(initHour) + str(initMins)
    bucketToCreate = "sudo s3cmd mb s3://" + folderToSave
    process = subprocess.Popen(bucketToCreate,shell=True, stdout=subprocess.PIPE)
    output = str(process.communicate())
    if 'created' in output:
        condition = 2
        print 'Bucket has been succesfully created'
    else:
        condition = 1
        print 'Bucket was not created'


#subprocess.Popen(bucketToCreate,shell=True).wait #os.system(bucketToCreate)
os.chdir("/home/pi/Data")
os.mkdir(folderToSave)
print folderToSave
print bucketToCreate
        
# Define the subroutines
def modification_date(filename):
    t = os.path.getmtime(filename)
    a = str(dt.datetime.fromtimestamp(t))
    a1 = a[:-7]
    a1 = a1.replace(":", "")
    a1 = a1.replace(" ", "_")
    return a1

def IpCamera():
    while True:
        print threading.currentThread().getName(), 'Starting'
        #Grab the current datetime which will be used to generate dynamic folder names
        e = datetime.now()
        initYear = "%04d" % (e.year) 
        initMonth = "%02d" % (e.month) 
        initDate = "%02d" % (e.day)
        initHour = "%02d" % (e.hour)
        initMins = "%02d" % (e.minute)
        initSecs = 0 # Set at zero to prevent continuous drift - this assumption is okay
        #avconvCommandTemp = "sudo ffmpeg -i rtsp://admin:password11@" + camAddress  + " -c copy -t 20 " + "/home/pi/Data/videoTemp.mp4"
        avconvCommandTemp = "cvlc rtsp://admin:password11@" + camAddress + " --run-time 30.00 --sout=file/ts:videoTemp.mp4 vlc://quit"
        #print avconvCommand
        #subprocess.Popen(avconvCommandTemp,shell=True).wait
        count = 1
        while count < 10: # Run this up to ten times
            subprocess.Popen(avconvCommandTemp,shell=True).wait # equivalent to calling os.system
            time.sleep(32)
            try:
                sizer2 = os.path.getsize("/home/pi/Data/videoTemp.mp4")
                if sizer2 > 500000: # bytes
                    shutil.copy2("/home/pi/Data/videoTemp.mp4", "/home/pi/Data/" + folderToSave + '/' + siteName + str(initYear) + str(initMonth) + str(initDate) + "_" + str(initHour) + str(initMins) + str(initSecs) + ".mp4")
                    time.sleep(1)
                    shutil.copy2("/home/pi/Data/videoTemp.mp4", "/home/pi/googledrive/" + siteName + str(initYear) + str(initMonth) + str(initDate) + "_" + str(initHour) + str(initMins) + str(initSecs) + ".mp4")
                    time.sleep(1)
                    os.system("sudo rm /home/pi/Data/videoTemp.mp4")
                    print "Video succesfully acquired"
                    break
                else:
                    os.system("sudo rm /home/pi/Data/videoTemp.mp4")
                    print "Video size less than 900kb, trying again"
                    time.sleep (1)
                    count = count + 1
            except OSError:
                print "No video acquired, OSError"
                count = count + 1
                pass

        f = datetime.now()
        initMins2 = "%02d" % (f.minute)
        initSecs2 = "%02d" % (f.second)
        bias = int(initSecs2) - initSecs # Calculate the timing bias
        time.sleep(zz*60 - bias) # Wait zz minutes before next capture minus bias produced during the photo capture to prevent timing drift
        print threading.currentThread().getName(), 'Exiting'
		
		
def PiCameraBaby(): # Image aquisition
    while True:
        print threading.currentThread().getName(), 'Starting'
        # Grab the current datetime which will be used to generate dynamic folder names
        e = datetime.now()
        initYear = "%04d" % (e.year) 
        initMonth = "%02d" % (e.month) 
        initDate = "%02d" % (e.day)
        initHour = "%02d" % (e.hour)
        initMins = "%02d" % (e.minute)
        initSecs = 0 # Set at zero to prevent continuous drift - this assumption is okay
        time.sleep(15) # Sleep for 15 seconds to allow the infrared light to power up

        # Assess the system demands and report as a html file for upload
        os.system("echo q | htop | aha --black --line-fix > " + str(folderToSave) + "/" + siteName + str(initYear) + str(initMonth) + str(initDate) + "_" + str(initHour) + str(initMins) + str(initSecs) + ".html")
       
        # Define the size of the image you wish to capture. 
        imgWidth = 2592 # Max = 2592 
        imgHeight = 1944 # Max = 1944
        print " --------- Saving file at " + initHour + ":" + initMins + " --------- "
            
        # Capture the image using raspistill. Set to capture with added sharpening, auto white balance and average metering mode
        # Change these settings where you see fit and to suit the conditions you are using the camera in
        os.system("raspivid -t 3000 -fps 30" + " -o " + str(folderToSave) + "/" + siteName + str(initYear) + str(initMonth) + str(initDate) + "_" + str(initHour) + str(initMins) + str(initSecs) + ".h264")

        # Take a final time reading and calculate the time taken to take the photo and save the data
        f = datetime.now()
        initMins2 = "%02d" % (f.minute)
        initSecs2 = "%02d" % (f.second)
        bias = int(initSecs2) - initSecs # Calculate the timing bias
        time.sleep(zz*60 - bias) # Wait zz minutes before next capture minus bias produced during the photo capture to prevent timing drift
        print threading.currentThread().getName(), 'Exiting'

def stageReading(): # Conduct the ultrasonic level reading
    while True:
        print threading.currentThread().getName(), 'Starting'
        g = datetime.now()
        initSecs = 0 # Set at zero to prevent continuous drift - this assumption is okay
        os.system("sudo killall -9 UltrasonicMeasurements")
        time.sleep (5) # sleep until the previous process has been stopped
        os.system("sudo /home/pi/cooking/arduPi/UltrasonicMeasurements") # Run the c++ script controlling the hardware
        time.sleep (15) # sleep for 15 seconds until the measurments have been made
        d = modification_date('/home/pi/Data/UltrasonicOutput.txt') # Find the date/time that the last measurement was made
        shutil.copy2("/home/pi/Data/UltrasonicOutput.txt", "/home/pi/Data/" + folderToSave + '/' + siteName + "_Level_" + str(d) + ".txt") # Create a copy of this data ready for upload
        # Take a final time reading and calculate the time taken to take the distance measurements and save the data
        h = datetime.now()
        initMins2 = "%02d" % (h.minute)
        initSecs2 = "%02d" % (h.second)
        bias = int(initSecs2) - initSecs # Calculate the timing bias
        time.sleep(1*60 - bias) # Wait 1 minute before next data aquisition minus bias produced during the last measurement to prevent timing drift
        print threading.currentThread().getName(), 'Exiting'

def uploadAll(): # Upload data to AWS
    counter = 0
    while True:
        os.system("ping -w 10 www.google.com > pingresult.txt");  #ping to google and display response
        sizer = os.path.getsize('/home/pi/Data/pingresult.txt')
        os.system('rm /home/pi/Data/pingresult.txt')  
        if sizer > 0:
            print threading.currentThread().getName(), 'Starting'
            itemsToRemove = os.listdir("/home/pi/Data/" + folderToSave + "/") # Specify the files being uploaded/deleted
            iter1 = len(itemsToRemove) # Number of files in the directory
            savePathAll = "sudo s3cmd sync " + "/home/pi/Data/" + folderToSave + "/" + " s3://" + folderToSave # Upload the newly generated files to the AWS
            os.system(savePathAll)

            # Generate the list of files already in the bucket
            pathCall = "sudo s3cmd ls s3://" + folderToSave 
            process = subprocess.Popen(pathCall,shell=True, stdout=subprocess.PIPE)
            output = str(process.communicate())

            print "---------- New data uploaded to AWS ----------"
            if iter1 > 0: # if there are files in the Data directory
                for x in range(0,iter1): # Run this for the number of files in the directory
                    if itemsToRemove[x] in output: # if the item in Data already exists in s3
                        os.remove("/home/pi/Data/" + folderToSave + "/" + itemsToRemove[x]) # Remove them one-by-one

            itemsToRemove2 = os.listdir("/home/pi/backupData/")
            iter2 = len(itemsToRemove2) # Number of files in the directory
            savePathAll2 = "sudo s3cmd sync " + "/home/pi/backupData/" + " s3://" + folderToSave # Upload the newly generated files to the AWS
            os.system(savePathAll2)
            print "---------- Backup data uploaded to AWS ----------"
            if iter2 > 0:
                for xx in range(0,iter2): # Remove each of the uploaded files through this loop:
                    if itemsToRemove2[xx] in output:
                        os.remove("/home/pi/backupData/" + itemsToRemove2[xx]) # Remove them one-by-one

            time.sleep(30) # After a succesful sync allow the upload routine to rest for thirty seconds before restarting
            counter = 0 # Reset the counter after success
            print threading.currentThread().getName(), 'Exiting'

        else:
            #subprocess.Popen("sudo wvdial",shell=True).wait # Run wvdial incase it has falled over
            counter = counter + 1
            time.sleep(30)

        if counter == 250:
            os.system("sudo reboot -h now"); 
			

              
# Find the next timestamp with a multiple of zz
a = range(0,60,zz); print(a)
z = int(initMins)
takeClosest = lambda num,collection:min(collection,key=lambda x:abs(x-num))
startAt = takeClosest(z,a)+zz
if startAt == 60:
    startAt = 0
print(startAt)

if 1 <= startAt <= 55:
    y = d.replace(minute=startAt, second =0, microsecond=0)
else:
    y = d.replace(hour = d.hour+1, minute=0, second=0, microsecond=0)

delta_t = y-d
secs = delta_t.seconds+1
print(secs) # Number of seconds until program executes
time.sleep(secs)

#Create new threads
thread4 = threading.Thread(name='uploadAll', target=uploadAll)
thread5 = threading.Thread(name='IpCamera', target=IpCamera)
thread7 = threading.Thread(name='gmx', target=gmx)


#Start new threads
thread4.start()
thread5.start()
thread7.start()


print "Exiting main thread"            

