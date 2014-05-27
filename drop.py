import dropbox
import pickle
import os
import time
import sys
import pprint

def touch(path):
    basedir = os.path.dirname(path)
    if not os.path.exists(basedir):
        os.makedirs(basedir)
    if os.path.isdir(path):
        return
    with open(path, 'a'):
        os.utime(path, None)

def symMap(rD):
    dir = client.metadata(rD)
    basepath = os.path.join(os.path.expanduser('~'),'Dropbox')
    for p in dir['contents']:
        if p['is_dir']:
            symMap(p['path'])
        else:
            touch(os.path.join(basepath, p['path'].replace('/','',1)))

def authenticate():
    if os.path.exists(os.path.expanduser('~/lib/db.auth')):
        return pickle.load(open(os.path.expanduser('~/lib/db.auth')))
    flow = dropbox.client.DropboxOAuth2FlowNoRedirect(key, secret)
    authorize_url = flow.start()
    print '1. Go to: ' + authorize_url
    print '2. Click "Allow" (you might have to log in first)'
    print '3. Copy the authorization code.'
    code = raw_input("Enter the authorization code here: ").strip()
    access_token, user_id = flow.finish(code)
    pickle.dump((access_token, user_id),open('db.auth','w'))
    return access_token, user_id

def listDir(dir):
    dir = client.metadata(dir)
    if dir['is_dir']:
        for item in dir['contents']:
            if item['is_dir']:
                print item['path'].split('/')[-1]+ '/'
            else:
                print item['path'].split('/')[-1]
    else:
        print dir['path'].split('/')[-1]

def sync(rD):
    lD = rD.split('/')[-1]
    if not os.path.exists(lD):
        os.mkdir(lD)
    rDls = [x for x in client.metadata(rD)['contents'] if not x['is_dir']]
    mod ={}
    for x in rDls:
        if not os.path.exists(lD+'/' + x['path'].split('/')[-1]) or makedbtime(x['modified']) > os.path.getmtime(lD+'/' + x['path'].split('/')[-1]):
            out = open(lD+'/' + x['path'].split('/')[-1], 'wb')
            out.write(client.get_file(x['path']).read())
            out.close()
    for f in os.listdir(lD):
        if f not in map(getFilename, rDls) and not os.path.isdir('/'.join([lD,f])):
            file = open('/'.join([lD,f]),'rb')
            data = client.put_file('/'.join([rD,f]),file,True)
            print 'Uploaded', f , 'to', data['path']
        mod['/'.join([lD,f])] = os.stat('/'.join([lD,f]))[-2]
    while True:
        time.sleep(3)
        for f in os.listdir(lD):
            try:
                if mod['/'.join([lD,f])] != os.stat('/'.join([lD,f]))[-2]:
                    mod['/'.join([lD,f])] = os.stat('/'.join([lD,f]))[-2]
                    file = open('/'.join([lD,f]),'rb')
                    data = client.put_file('/'.join([rD,f]),file,True)
                    print 'Uploaded to \''+ data['path'] + '\''
                    file.close()
            except KeyError:
                mod['/'.join([lD,f])] = os.stat('/'.join([lD,f]))[-2]

def makedbtime(s):
    return time.mktime(time.strptime(s,"%a, %d %b %Y %H:%M:%S +0000"))

def getFilename(path):
    return path['path'].split('/')[-1]

def quickPut(i, o, over):
    path = client.metadata(o)
    f = open(i, 'rb')
    if path['is_dir']:
        data = client.put_file('/'.join([o,i.split('/')[-1]]), f, overwrite=over)
    else:
        data = client.put_file(o, f, overwrite=over)
    print 'Uploaded to \'' + data['path'] + '\''

def quickGet(f, recursive=False):
    data = client.metadata(f)
    curDir = os.getcwd()
    if data['is_dir']:
        if curDir.split('/')[-1] != data['path'].split('/')[-1]:
            if not os.path.exists(data['path'].split('/')[-1]):
                os.mkdir(data['path'].split('/')[-1])
            os.chdir(data['path'].split('/')[-1])
        for i in data['contents']:
            if i['is_dir'] and recursive:
                if not os.path.exists(i['path'].split('/')[-1]):
                    os.mkdir(i['path'].split('/')[-1])
                os.chdir(i['path'].split('/')[-1])
                quickGet(i['path'], recursive)
                os.chdir('..')
            if not i['is_dir']:
                out = open(i['path'].split('/')[-1],'wb')
                out.write(client.get_file(i['path']).read())
                out.close()
    else:
        out = open(f.split('/')[-1], 'wb')
        out.write(client.get_file(f).read())
        out.close()
        print 'Downloaded \'' + out.name + '\' from \'' + f + '\''

key = 'g3uu5vbgzb295dw'
secret = 'xqnukbih7rlerzl'
ac, id = authenticate()
client = dropbox.client.DropboxClient(ac)

if __name__=='__main__':
    if '-s' in sys.argv:
        rD = sys.argv[sys.argv.index('-s')+1].replace(os.path.expanduser('~')+'/Dropbox','')
        sync(rD)
    elif '-g' in sys.argv:
        quickGet(sys.argv[sys.argv.index('-g')+1].replace(os.path.expanduser('~')+'/Dropbox',''))
    elif '-gR' in sys.argv:
        quickGet(sys.argv[sys.argv.index('-gR')+1].replace(os.path.expanduser('~')+'/Dropbox',''), True)
    elif '-p' in sys.argv:
        try:
            i, o = sys.argv[sys.argv.index('-p')+1:]
            quickPut(i, o.replace(os.path.expanduser('~')+'/Dropbox',''), False)
        except ValueError:
            print "Need local, then remote location for -p option"
    elif '-op' in sys.argv:
        try:
            i, o = sys.argv[sys.argv.index('-op')+1:]
            quickPut(i, o.replace(os.path.expanduser('~')+'/Dropbox',''), True)
        except ValueError:
            print "Need local, then remote location for -op option"
    elif '-ls' in sys.argv:
        try:
            dir, = sys.argv[sys.argv.index('-ls')+1:]
            listDir(dir.replace(os.expanduser('~')+'/Dropbox'),'')
        except ValueError:
            print "Need directory to list"
    elif '-map' in sys.argv:
        arg, d= sys.argv[sys.argv.index('-map'):]
        symMap(d)
    else:
        print "Commands:\n\t"+'-s'.ljust(len('--help'),' ')+" Download a directory non-recurisvely and monitor changes\n\t"+'-g'.ljust(len('--help'),' ')+" Perform a get on [arg1]\n\t"+'-p'.ljust(len('--help'),' ')+" Put [arg1] in [arg2]\n\t"+'-ls'.ljust(len('--help'),' ')+" List directory\n\t"+'-op'.ljust(len('--help'),' ')+" Put [arg1] in [arg2] with overwrite\n\t--help Print this message"
