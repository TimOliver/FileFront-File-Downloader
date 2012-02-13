#!/usr/bin/env python
# A quick and VERY DIRTY filefront file ripper.
# LJ
#
# Enhanced by TiM of UberGames, November 2011
# (My first time with Python. Apologies in advance for the terrifying code. ^_^;)
#
# Changes Made:
#       - Rewrote parse code for FileFront frontend HTML templates (circa November 2011)
#       - Upgraded to handle FileFront's download manager (circa November 2011)
#       - Can download categories that span multiple pages
#       - Has the option of automatically downloading any subcategories in the current category as well
#       - Organizes downloaded files in a folder hierarchy matching the web site
#       - Downloads any available screenshots attached to files
# 

import urllib2
import os
import os.path
import random
import re

# The local directory to download all of the files to (must be absolute)
downloadDirectory = "/Users/TiM/Desktop/FileFrontDownloads"

# The base URL for the target FileFront site
siteRoot = "http://eliteforce2.filefront.com"

# An array of all of the categories/subcategories pages that are to be downloaded
categoryLinks = [ "/files/Elite_Force;4index", "/files/Elite_Force_2;26index" ]

# An array of extra file links to download
fileLinks = []

# If the category has sub-categories, it'll drop down and download those too
downloadSubCategories = True

def formatFileName(sFileName):
        if len(sFileName) <= 0:
                return ''
        
        # Replace all spaces with underscores
        sFileName = sFileName.replace( ' ', '_' )

        # Remove all other non-standard characters
        sFileName = re.sub( '[^a-zA-Z0-9_\-\.]', '', sFileName )

        return sFileName

def makeFolderPath( aFolderNames ):
        global downloadDirectory

        path = downloadDirectory

        # navigate to the base folder
        os.popen( ("cd " + downloadDirectory) )

        # Loop through each folder, create it if it doesn't exist, and append to the final path
        for folderName in aFolderNames:
                folderName = formatFileName( folderName )
                path = path + '/' + '_' + folderName

                if os.path.exists( path ) == False:
                         os.popen( 'mkdir ' + path )
                
                os.popen( 'cd ' + path )
                
        os.popen( ("cd " + downloadDirectory) )

        return path

def getNames(sPage):
        # Get a list of mod names from the page.
        pPage = urllib2.urlopen(sPage)
        pPageContent = str( pPage.read() )
       
        # Find the link.
        print "Looking for links..."

        lLinks = []
        
        # Looks like all of the file links are now rendered
        # without line-breaks. Better break out the regex!
        p = re.compile('<b><a class="size11" href="(/file/[^"]+)')
        reLinks = p.findall( pPageContent ) # searching for instance of '<a href="(/file/Lt_Kulhane;26594)">'

        # TiM: There are some redundant links like '#comments' that we can skip
        for sLink in reLinks:
                if sLink.find('#') == -1:
                        lLinks.append( sLink ) 
                        # print (sLink)

        # print len(lLinks)

        return lLinks
        
def doDownload(sPage, sDownloadRoute ):
        global siteRoot
        global downloadDirectory

        sCommand = "wget --user-agent='Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.8.1.5) Gecko/2007071317 Firefox/2.0.0.5' "
        # --load-cookies="+downloadDirectory+"/cookies.txt

        print ""
        print "***********************************************************"
        print "Downloading "+sPage

        # Download the file profile page
        sLink = ( siteRoot + sPage )
        pPageContent = urllib2.urlopen(sLink).read()
        
        # Since it's possible for files to have both identical names and file names,
        # we'll load them down via their ID numbers
        fileID = sPage.split(';')[1]

        # Get the file name
        m = re.search( r'<span class="size14"><u>([^<]+)</u></span>', pPageContent )
        if m == False:
                return

        sFileName = m.group( 1 ).strip()
        
        # All source files will be placed in a folder like 'Filename - ID'
        sFolderName = formatFileName( sFileName + '-' + str( fileID ) )
        
        sDownloadRoute = sDownloadRoute + '/' + sFolderName
        os.popen( 'mkdir ' + sDownloadRoute )

        # Perform a search for any screenshots on the page and download any that have been found
        print ""
        print "Checking for Screenshots"

        p = re.compile( '<a href="/screenshots/File/[^"]+"[^>]+><img src="([^_]+_[0-9]+)t.jpg"' )
        lScreenshots = p.findall( pPageContent )
        print str( len(lScreenshots) ) + " screenshots found"

        if len( lScreenshots ) > 0:
                i = 1
                for sScreenshot in lScreenshots:
                        print "Downloading screenshot #" + str( i )
                        sScreenshot = sScreenshot + '.jpg'

                        os.chdir(sDownloadRoute)
                        os.popen( (sCommand + " --output-document='screenshot_"+str(i)+".jpg' " + sScreenshot) )
                        i = i+1
                
                print "Screenshot Downloads Completed"
                print "" 


        # Find the link.
        print "Searching for File Download Link"
        
        m = re.search( r'<a class="size16" href="(/file/gofetch/[^"]+)', pPageContent )
        if m == False:
                print "Unable to locate Download Link"
                return

        # Jump to the FileFront file download prompt and download it
        print "Loading GameFront Download Portal"
        sDownloadPortalURL = (siteRoot + m.group( 1 )).strip()
        sDownloadPortalPage= urllib2.urlopen( sDownloadPortalURL )
        sDownloadPortalPageContent = sDownloadPortalPage.read()

        # Preserve the session ID that gets generated with this request
        # Otherwise, the next one will kick us back home
        setCookie = sDownloadPortalPage.headers.getheader("Set-Cookie")
        sessId = setCookie[setCookie.index("=")+1:setCookie.index(";")]
        headers = { "Cookie": "PHPSESSID="+sessId }

        # Go to the actual Download page
        print "Loading GameFront Download Page"
        m = re.search( r'(http://www.gamefront.com/files/service/thankyou\?id=[0-9]+)', sDownloadPortalPageContent )
        sDownloadMirrorURL = m.group( 1 ).strip()
        sDownloadMirrorPageContent = urllib2.urlopen( urllib2.Request(sDownloadMirrorURL, headers=headers) ).read()

        # Grab the download link from the 'click here' button
        m = re.search( r'<br />If it does not, <a href="([^"]+)">click here', sDownloadMirrorPageContent )
        if m == False:
                return

        sModFile = m.group( 1 ).strip()
        sFileName = sModFile[ sModFile.rfind('/')+1:sModFile.rfind('?') ]

        # Download the file.
        os.chdir(sDownloadRoute)
        
        print "Downloading HTML File - " + sFolderName+"_page.html"
        os.popen((sCommand + " --output-document='"+sFolderName+"_page.html' '" + sLink+'x' + "'") ) # Adding an x expands all comments... apparently
        
        print "Downloading File - " + sFileName
        os.popen((sCommand + " --output-document='"+sFileName+"' '" + sModFile + "'") )

        print "File Download Complete"
        print "***********************************************************"


def downloadCatagoryPage(sCatPath):
        global siteRoot
        global downloadSubCategories

        # Download the base page
        sFullPath = (siteRoot + sCatPath)
        pPageContent = urllib2.urlopen( sFullPath ).read()

        # calculate the subcategory structure from the root
        p = re.compile( '<a class="browser_head"[^>]+>([^<]+)' )
        parentCategories = p.findall( pPageContent )
        sDownloadPath = makeFolderPath( parentCategories )

        # if the list of files spans multiple pages, be sure to loop through each one
        start = 0;
        i = 1
        while True:
                #build the sCatPath in full, including root URL and sort parameters
                sFullCatPath = (siteRoot + sCatPath+"?&sort=name&name_direction=asc&limit=100&start=" + str(start) )

                lLinks = getNames(sFullCatPath)
                if lLinks == False:
                        print "Unable to parse page: "+sCatPath
                        return

                print str( len(lLinks) ) + " links found on page " + str( i )

                for sLink in lLinks:
                        try:
                                doDownload(sLink, sDownloadPath)
                        except:
                                "error downloading" + str(sLink)

                break

                # terminate the loop if the list has less than 100 entries
                if len(lLinks) < 100:
                        break 

                start += 100
                i = i+1

        # If requested, download the Sub-categories as well
        if downloadSubCategories == True:
                p = re.compile('<a class="size16" href="([^"]+)" title="[^"]+"><img src="/skins/icons/expand.gif"')
                subCategoryLinks = p.findall( pPageContent )

                if len( subCategoryLinks ) > 0:
                        print ""
                        print str( len(subCategoryLinks) ) + " subcategories found."

                        for subCategoryLink in subCategoryLinks:
                                print "Downloading subcategory: " + subCategoryLink
                                downloadCatagoryPage( subCategoryLink )


## *********************************************************************************
## FILEFRONT RIPPER ENTRY POINT

print ""
print "***********************************************************"
print "| FileFront File Ripper"
print "| November 2011 "
print "| By LJ "
print "| Changes/Enhancements by TiM (http://www.ubergames.net/)"
print "***********************************************************"
print ""

os.chdir( downloadDirectory )

# Download all of the pages
for sLink in categoryLinks:
        print "Downloading Category: " + sLink
        downloadCatagoryPage(sLink)

for sLink in fileLinks:
        print "Downloading File: " + sLink
        doDownload( sLink, downloadDirectory )