#!/usr/bin/env python
import os
import shutil, errno
import subprocess
import smtplib
import time
import sys
import re
import shlex
from email.MIMEMultipart import MIMEMultipart
from email.MIMEText import MIMEText

#-------------------------------------------------------------------

#colors and question logic


def blue(text):
    a ='\033[1;34m%s\033[1;m' % text
    return (a)

def red(text):
    a= '\033[1;31m%s\033[1;m' % text
    return (a)

def query_yes_no(question, default=None):
    valid = {"yes":True,   "y":True,  "ye":True,"no":False,     "n":False}
    if default == None:
        prompt = red(" [y/n] ")
    elif default == "yes":
        prompt = " [Y/n] "
    elif default == "no":
        prompt = " [y/N] "
    else:
        raise ValueError("invalid default answer: '%s'" % default)

    while True:
        sys.stdout.write(question + prompt)
        choice = raw_input().lower()
        if default is not None and choice == '':
            return valid[default]
        elif choice in valid:
            return valid[choice]
        else:
            sys.stdout.write("Please respond with 'yes' or 'no' "\
                             "(or 'y' or 'n').\n")

            
#-------------------------------------------------------------------#

#Pre-Processing

def free(home):
    disk = os.statvfs(home)
    free = disk.f_bsize*disk.f_bavail/1.073741824e9
    free = str(free).split('.').pop(0)
    return free

def used_space(home):
    disk = os.statvfs(home)
    used = disk.f_bsize * (disk.f_blocks - disk.f_bavail)/1.073741824e9
    used = str(used).split('.').pop(0)
    return used

def args():
    if len(sys.argv) > 1:
        if str(sys.argv[1]) == '-ne':
            return 'ne'
        else:
            return '0'

def PreProcess(file_path, working_dir):
    for show in os.listdir(file_path): 
        item = file_path+ '/' + show #file_path/folder
        if os.path.isdir(item):  # if item is a directory
            shows = extract(item, show, working_dir)
            print shows
            if len(shows) != 0:
               for s in shows:
                   os.rename(file_path+'/'+show+'/'+s, working_dir+'/'+s)
        else:
            print item + ' is not a folder!'
            print item +' '+ working_dir+'/'+show
            os.rename(item, working_dir+'/'+show)
            
            
    return

def AnyMovies(working_dir):
    shows=[]
    movies=[]
    if query_yes_no('\n'+'Any movies?: '):
        for f in os.listdir(working_dir):
            if query_yes_no('Is %s a movie?: ' % f):
                movies.append(f)
            else:
                shows.append(f)
    else:
        return ('yes','none')
    
    return (shows, movies)

def FixMovies(movies, working_dir):
    new_movies = []
    if movies != 'none':
        for movie in movies:
            new_movie = fix_movie(movie)
            new_movies.append(new_movie)
            os.rename(working_dir + '/%s' % (movie), working_dir + '/%s' % (new_movie)) # rename file_path/newshows01e04.mkv to file_path/newshow-s01e04.mkv
        return new_movies
    return

def FixShows(shows, working_dir):
    if shows != 'yes':
        for show in shows:
            if show.endswith('store'):
                shows.remove(show)
            new, flag = fix_name(show) # newshows01e04.mkv returned
            new2 = fix_name_2(new, flag) # newshow-s01e04.mkv returned
            os.rename(working_dir + '/%s' % (show), working_dir + '/%s' % (new2)) # rename file_path/newshows01e04.mkv to file_path/newshow-s01e04.mkv
    else:
        shows = os.listdir(working_dir)
        for show in shows:
            new, flag = fix_name(show) # newshows01e04.mkv returned
            new2 = fix_name_2(new, flag) # newshow-s01e04.mkv returned
            os.rename(working_dir + '/%s' % (show), working_dir + '/%s' % (new2))# rename file_path/newshows01e04.mkv to file_path/newshow-s01e04.mkv
    return
#--------------------------------------------------------------------#
            
# extracting


#handles all of the extraction
def extract(show, show_name, working_dir): #file_path/folder , show name
    shows = []
    print blue('\n'+'working on '+show_name)
    files = os.listdir(show) #list of sub files in file_path/folder
    for file in files: # for sub files in file_path/folder
        if os.path.isfile(show + '/' + file): #if the sub file is a file
            if file.startswith('samp'): #lokk for sample files
                print red('Found possible sample file %s' % (show_name))
                byte_size = os.path.getsize(show + '/' + file)
                print red(byte_size)
                if query_yes_no(blue('Would you like to skip this file?: ')):
                    pass
                else:
                    shows.append(file)
            elif file.endswith('rar'):
                unrar(file, show, working_dir) # pass to unrar func 
                break
            elif file.endswith('mkv'):
                os.rename(show+'/'+file, working_dir+'/'+file)
            elif file.endswith('mp4'):
                os.rename(fshow+'/'+file, working_dir+'/'+file)
            elif file.endswith('avi'):
                os.rename(show+'/'+file, working_dir+'/'+file)
            else:
                pass
        elif os.path.isdir(show+'/'+file): #file_path/folder/subFolder
            print show+'/'+file
            extract(show+'/'+file, file, working_dir) # recursion, haven't had this happend often but works          
    return shows #returns file_path/folder, list of files

#sub function of extract.  Used to rar the files back together if need be
def unrar(file, show, working_dir):
    file = show + '/' + file
    fnull = open(os.devnull, 'w')
    unrar_cmd = subprocess.call(['rar', 'x', '-kb','%s' % (file), working_dir], stdout=fnull)
    return


#--------------------------------------------

# naming

#for files you say are movies
def fix_movie(movie):
    extension = os.path.splitext(movie)[1] #determine extension
    movie.replace(extension,"") #replace the extension so that it doesn't mess up the regex
    try:
        regex = re.findall('\.'+'[0-9]', movie).pop(0) #not the best but works, find '.' and any number in movie and pop
    except IndexError:
        #regex = re.findall('\s'+'[0-9]', movie).pop(0) #handle whitespace
        return movie
    index = movie.index(regex) #set the regex position as an int
    movie = movie[:index] + extension #split the movie so that all the garbage is removed. ie All.Is.Lost.2013.DVDScr.XVID.AC#.HQ.HIVE-CM8.avi
    #would end up being All.Is.Lost.avi
    return movie
    

#this is stage one of renaming show

def fix_name(self): #file name ex: new.show.s01e04.hdtv.720p.mkv
    if self == '.ds_store':
        return self, '0'
    self = self.lower() #make lower
    extension = os.path.splitext(self)[1] #determine extension
    self = self.replace(extension,"")  #replace extension
    try:
        self = self.replace('-','') # new.shows.01e04.hdtv.720p
        self = self.replace('.', '') # newshows01e04hdtv720p
        self = self.replace('season', 's') # newshows01e04hdtv720p
        self = self.replace('episode', 'e')# newshows01e04hdtv720p
        regex = re.findall('s'+'[0-9]', self).pop(0) # 's0'
        index_for_dash = self.index(regex)  #starts at s  (7)
        stage = index_for_dash + 6 # value (7+6 = 13)
        self = self[:stage] # counts 13 chars in and then adds extension 'newshows01e04.mkv'
    except IndexError:
        if extension == ".m4v": #this caused me issues once so it is in here....
            return (self, '1') #flag 1 is used for some understanding later...allows me to track what exceptions a file hit
        else:
            try: #this exception is invoked when the file does not have one of the above replace statments
                regex = re.findall('[a-z]'+'[0-9]', self).pop(0)#this regex needs to be revistied but it works %95 of the time.
                index_for_dash = self.index(regex) 
                stage = index_for_dash+1
                self = self[:stage]
                self = self+extension
                return (self, '1')#flag 1 is used for some understanding later...allows me to track what exceptions a file hit
            except IndexError:
                self = self+extension  # this will hit if the file is really different and the regex didn't hit.  Never had this hit.
                return (self, '1')#flag 1 is used for some understanding later...allows me to track what exceptions a file hit
    return (self+extension, '0') #newshow-s01e04.mkv


#This function is used for the final placement of the '-'.  Honestly i could revisit this and remove it but for now I am fine with it

def fix_name_2(self, flag):  #newshows01e04.mkv, 0 or 1
 
    if flag == '1': #flag 1 says 'Hey look I cant determine a season and or episode so you tell'
        whole_show = self
        extension = os.path.splitext(self)[1]
        self = self.replace(extension,"")
        show_folders = os.listdir(production)
        for show in show_folders:
            try:
                if show.replace(' ',"").lower() == self:
                    get_seasons = os.listdir(production + '/' + show)
                    get_most_recent_season = get_seasons.pop(-1)
                    path_to_shows = os.listdir(production + '/' + show + '/' + get_most_recent_season)
                    most_recent = path_to_shows.pop(-1)
                    if most_recent.endswith('mkv'):
                        print blue("Need help with ")  + red(self) + '.  The most recent show is ' + red(most_recent)
                    elif most_recent.endswith('mp4'):
                        print blue("Need help with ")  + red(self) + '.  The most recent show is ' + red(most_recent)
                    elif most_recent.endswith('avi'):
                        print blue("Need help with ")  + red(self) + '.  The most recent show is ' + red(most_recent)
                    else:
                        most_recent = path_to_shows.pop(-1)
                        print blue("Need help with ")  + red(self) + '.  The most recent show is ' + red(most_recent)
            except IndexError:
                print "No prior shows found for "+ whole_show
                season = raw_input('Enter Season (i.e. 01, 02): ') #ie '01'
                episode = raw_input('Enter episode (i.e. 01, 02): ')# ie '01'
                self = self+'-s%se%s%s'% (season, episode, extension) #finished example 'newshow-s01e01.mkv'
                return self
        season = raw_input('Enter Season (i.e. 01, 02): ') #ie '01'
        episode = raw_input('Enter episode (i.e. 01, 02): ')# ie '01'
        self = self+'-s%se%s%s'% (season, episode, extension) #finished example 'newshow-s01e01.mkv'
        return self
    else: #anyother flag, which is only 0
        if self == '.ds_store':  #fuck you .ds_store
            return self
        try:
            regex = re.findall('s'+'[0-9]', self).pop(0) # 's0' we need a to know the base pointer for this insert we are about to do
            index_for_dash = self.index(regex)  # int the regex result.  ie. newshows01e04.mkv (7)
            self = self[:index_for_dash] + '-' + self[index_for_dash:] # read in 7 chars 'w' add '-' add the rest 'newshow-s01e04.mkv'
            self = check_for_ss(self)
            self = check_for_e00(self)
        except IndexError: #'s0' was not in the name and somehow the flag was not set above
            fix2(self,'1') #recursion with flag set
    return self #newshow-s01e04.mkv  I dont even think this is ever hit hahaha lots of legacy shit in here


def check_for_ss(self):
    print 'Running checks on '+self
    time.sleep(2)
    check_in = self.split('-').pop(0)
    if check_in.endswith('s'):
        if query_yes_no('Does the show name need an extra s?: '):
            first = self.split('-')[0]
            first = first+'s'
            end = self.split('-')[1]
            self = first+'-'+end
            print 'Found double s, fixed!'
    else:
        return self
    return self


def check_for_e00(self):
    check_two = self.split('.').pop(0)
    if check_two[-1:].isdigit():
        if check_two[-3:].startswith('e'):
            print '====> File name is good!'
            time.sleep(1)
            return self
        else:
            print 'Episode format is not correct for '+self
            first = self.split('-')[0]
            end = self.split('-')[1].split('.')[1]
            season = raw_input('Enter Season (i.e. 01, 02): ') #ie '01'
            episode = raw_input('Enter episode (i.e. 01, 02): ')# ie '01'
            self = first+'-s%se%s%.s'% (season, episode, end)
            print 'New Name is '+self
            time.sleep(1)
            return self
    else:
        print 'Regex failed!'
        first = self.split('-')[0]
        end = self.split('-')[1].split('.')[1]
        if query_yes_no('Does the show name need an extra s?: '):
            first = first+'s'
        season = raw_input('Enter Season (i.e. 01, 02): ') #ie '01'
        episode = raw_input('Enter episode (i.e. 01, 02): ')# ie '01'
        self = first+'-s%se%s.%s'% (season, episode, end)
        print 'New Name is '+self
        time.sleep(1)
        return self
        

#------------------------------------------------------------------------------------------------

#mail time

def for_mail(working_dir, production):
    show_dict = {}
    new_shows = []
    holding_files = []
    files = os.listdir(working_dir) # list of holding files renamed my example /media/ntfsdrive1/Holding
    shows = os.listdir(production) # list of all tv show folders, use this to determine what new shows were added.

    #determine what the name of these shows are
    for f in files:
        name = f.split('-')[0] # newshow-s01e04.mkv = newshow
        holding_files.append(name) # append 'newshow' to list 
        holding_files = list(set(holding_files)) # remove any doubles, for example two episodes of one show.  We dont want to list the show in the email twice

    #now lets have fun with dictionaries         
    for show in shows:
        show_dict[show] = show.lower().replace(' ', '') # takes folder name from directory and sets it as the key and value = folder name lower no spaces
    
    for k,v in show_dict.iteritems(): # for pair in dict
        if v in holding_files: # if value is in the list of new show names
            new_shows.append(k) # then append the folder name to a new list
            holding_files.remove(v) # remove the file if we have iter'd it, otherwise it gets annoying
    if len(holding_files) != 0:# was 1
        return (holding_files,new_shows) # list of new show names, list of folder names
    else:
        return ('None', new_shows)  

def sendmail(movies, tv_shows):  # self explains, just sends out an email.
    if 'ds_store' in movies:
        movies.remove('ds_store')
    if '.DS_Store' in movies:  # fuck you DS_store, gtfo
        movies.remove('.DS_Store')
    #hey we need to handle movies because they dont have folders
    Movies = []
    for f in movies:
        extension = os.path.splitext(f)[1]
        try:
            if f.endswith('mkv'):
                f = f.strip('mkv') 
            elif file.endswith('mp4'):
                f = f.strip('mp4') 
            elif file.endswith('avi'):
                f = f.strip('avi')
        except AttributeError:
            pass
        Movies.append(f)
    print '\n'+'Here is the draft email'+'\n'            
    print '\n'.join(Movies)+'\n'  #make'em neat
    print '\n'.join(tv_shows)+'\n'#make'em neat
    if query_yes_no('Would you like to send the email?: '):
        recp = ['']  #list your friends email here comma seperated
        for r in recp:
            print 'Sending to '+ r
        for r in recp:
            user = '' # enter email address
            recipient = r
            message = 'The following new shows have been updated.'
            message_shows = '\n'.join(tv_shows)
            message_2 = 'The following movies were added.'
            message_movies = '\n'.join(Movies)
            message_end = 'Let me now if you want something added!  This is an automated message from a mailbox that I dont check often.'
            if 'ds_store' in message:
                message.remove('ds_store')
            COMMASPACE = ', '
            date = (time.strftime("%m/%d/%Y"))


            msg = MIMEMultipart()
            msg['From'] = user
            msg['To'] = r
            msg['Subject'] = 'Plex Updates for '+date  
            msg.attach(MIMEText(message+'\n'+'\n'+message_shows+'\n'+'\n'+message_2+'\n'+'\n'+message_movies+'\n'+'\n'+message_end))
              
            # Credentials (if needed)  
            username = '' # enter eamil address
            password = '' # enter email password
              
            # The actual mail send  
            mailServer = smtplib.SMTP('smtp.gmail.com:587')# this worked on CentOS with no configuration needed.
            mailServer.ehlo()
            mailServer.starttls()
            mailServer.ehlo()
            mailServer.login(username,password)  
            mailServer.sendmail(username, recipient, msg.as_string())  
            mailServer.close()
    else:
        return

def auto_move(production, working_dir, new_movies, production_movies):
    folders = os.listdir(production)
    files = os.listdir(working_dir)
    if query_yes_no('Would you like to move the file(s)?: '):
        print 'Auto Moving file(s)'
        if new_movies != 'none':
            try:
                for m in new_movies:
                    print 'Moving '+m+' to '+production_movies
                    os.rename(working_dir+'/'+m, production_movies)
            except TypeError:
                pass
        for f in files:
            regex = re.findall('-s'+'[0-9]', f).pop(0) # newshow-s01e01.mkv should find -s
            index = f.index(regex) + 2
            if f[index] == '0':
                index = f[index+1]
            else:
                index = f[index]+f[index+1]
            show_name = f.split('-').pop(0)
            for show in folders:
                if show.replace(' ',"").lower() == show_name:
                    cmd =  ([working_dir+'/'+f, production+'/'+show+'/Season '+index])
                    print 'Moving '+f+' to '+show+'/Season '+index
                    time.sleep(2)
                    #if query_yes_no('Would you like to move the file?: '):
                    os.rename(working_dir+'/'+f, production+'/'+show+'/Season '+index+'/'+f)
    else:
        print red('Not moving file')

def cleanup(file_path):
    if query_yes_no('cleanup?: '):
        for f in os.listdir(file_path):
            try:
                shutil.rmtree(file_path+'/'+f)
            except OSError as e:
                print 'Not a dir '+ file_path+'/'+f +' delete'
                print e
    return
            
#----------------------------------------------------------------------------------------------------------

#main
home = '' # Path to hard drive that stores your media, can be omitted
production_movies = '' # Full Path to your plex movies
production = '' #Full Path to your plex tv shows
file_path  = '' #Full path to holding location, where torrents will be downloaded to.
working_dir = '' #Full path to a working directory where torrents will be processed and their output moved to.

space = free(home) # omitt if no home path is specified
used = used_space(home) # omitt if no home path is specified


print '\n'+'######################################'
print '#  Welcome to your PLEX file script  #'
print '######################################'+'\n'
print '#########################'
print '#    PLEX HDD STATS     #'
print '#  Free space = '+space+'GB   #'
print '#  Used space = '+used+'GB  #'
print '#########################'+'\n'
time.sleep(1)



argv = args()
if argv == 'ne': #no extract, use if you dont want to work on the torrent files.  Instead this will work straight from the working_dir
    shows, movies = AnyMovies(working_dir)
    new_movies = FixMovies(movies, working_dir)
    FixShows(shows, working_dir)           
    hold_files, new_files = for_mail(working_dir, production)
    sendmail(hold_files, new_files)
    auto_move(production,working_dir, new_movies, production_movies)
    cleanup(file_path)
    space = free(home)
    print 'Free space = '+space+'GB'
else:
    PreProcess(file_path, working_dir)
    shows, movies = AnyMovies(working_dir)
    new_movies = FixMovies(movies, working_dir)
    FixShows(shows, working_dir)           
    hold_files, new_files = for_mail(working_dir, production)
    sendmail(hold_files, new_files)
    auto_move(production,working_dir, new_movies, production_movies)
    cleanup(file_path)
    space = free(home)
    print 'Free space = '+space+'GB'
