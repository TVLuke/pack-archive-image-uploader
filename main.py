import internetarchive as ia
import glob
import json
import time
import shutil
import random

directory_of_images = {}

image_folder = 'testimages'

# mostly debugging, to figure out what values exist...
licenses = set()
tags = set()

#how many times in a row did the upload fail?
errorcount = 0


def prepare_directory():
    jsonfiles = []
    for file in glob.glob("./metadata/*.json"):
        jsonfiles.append(file)

    for jsonfile in jsonfiles:
        print(len(jsonfiles))
        print(jsonfile)
        pure_filename = jsonfile.split('/')[-1]
        if pure_filename.startswith("photo_"):
            f = open(jsonfile)
            data = json.load(f)
            # print(data)
            imagefilename = data['id']
            print(imagefilename)
            print(data['license'])
            licenses.add(data['license'])
            for tag in data['tags']:
                tags.add(tag['tag'])
            directory_of_images[imagefilename] = jsonfile
            f.close()


def ia_access_tokens():
    token = "access_key:secret_key"
    return token.split(":")


def actual_upload(name, path, md, **kw):
    print("-------------------")
    print(name)
    print(path)
    print(md)
    # print(**kw)
    item = ia.get_item(name)
    r = item.upload(path, metadata=md, **kw)
    print(r[0].status_code)


def upload_images():
    access_key, secret_key = ia_access_tokens()
    print(access_key)
    print(secret_key)
    image_files = []
    for file in glob.glob("./" + image_folder + "/*"):
        image_files.append(file)

    # sometimes if the image names are similar the spam filter seeems to be triggered (I think, it's hard to tell)
    random.shuffle(image_files)
    for image_file in image_files:
        pure_filename = image_file.split('/')[-1].split('.')[0].replace('_o', '').split('_')[-1]
        print("Pure filename: "+pure_filename)
        if pure_filename not in directory_of_images:
            continue
        json_file_for_image = directory_of_images[pure_filename]
        f = open(json_file_for_image)
        data = json.load(f)

        i_name = data['name'].replace(' ', '_')

        # having a description massively reduces the likelihood of being flagged as spam
        i_description = data['description']
        i_description = i_description + '<br>' + i_name
        for album in data['albums']:
            i_description = i_description + '<br> - Album: ' + album['title']
        i_description = i_description + '<br><br><i>This is an item from the StudentenPACK-Image-Archive. Originally hosted on flickr.<br>The StudentenPACK was a Student Newspaper from Lübeck (Germany) running from 2005 to 2018. In Addition to print journalism dozens of student photographers published their work via the Newspaper. This archive preserves their work.</i><br><i>Dies ist ein Artikel aus dem StudentenPACK-Bilderarchiv. Ursprünglich gehostet auf flickr. Das StudentenPACK war eine studentische Zeitung an der Universität zu Lübeck (Deutschland), die von 2005 bis 2018 erschien. Neben dem Printjournalismus veröffentlichten Dutzende von studentischen Fotografen ihre Arbeiten über die Zeitung. Dieses Archiv bewahrt ihre Arbeiten auf.</i><br><br> https://www.studentenpack.de/'
        if data['photopage']:
            i_description = i_description + '<br> Originally Uploaded to: <a href="' + data['photopage'] + '">' + data[
                'photopage'] + '</a> on ' + data[
                                'date_imported']
        i_description = i_description.strip()

        i_subject = []

        i_tags = []
        i_creator = "StudentenPACK"
        i_license = data['license']
        if data['date_taken']:
            i_date = data['date_taken']
        else:
            i_date = data['date_imported']
        for tag in data['tags']:
            i_tags.append(tag['tag'])
            if tag['tag'].startswith("Foto:") or tag['tag'].startswith("foto:") or tag['tag'].startswith("Foo:"):
                if tag['tag'].startswith("Foto:"):
                    i_creator = tag['tag'].split("Foto:")[1]
                if tag['tag'].startswith("foto:"):
                    i_creator = tag['tag'].split("foto:")[1]
                if tag['tag'].startswith("Foo:"):
                    i_creator = tag['tag'].split("Foo:")[1]
                if not i_creator == "StudentenPACK":
                    i_creator = ''.join(map(lambda x: x if x.islower() else " " + x, i_creator))
                i_creator = i_creator.strip()
                if i_creator == 'Lukasruge':
                    i_creator = 'Lukas Ruge'
                if i_creator == 'albertpiek':
                    i_creator = 'Albert Piek'
                if i_creator == 'Sarah   Sandmann':
                    i_creator = 'Sarah Sandmann'
                if i_creator == 'Sora   Enders - Comberg':
                    i_creator = 'Sora Enders-Comberg'
                if i_creator == 'Sylvia   Kiencke':
                    i_creator = 'Sylvia Kiencke'
            else:
                i_subject.append(tag['tag'])
                if tag['tag'] == 'unilübeck':
                    i_subject.append("Uni Lübeck")
                if tag['tag'] == 'unilebeck':
                    i_subject.append("Uni Lübeck")
                if tag['tag'] == 'lübeck':
                    i_subject.append("Lübeck")
                if tag['tag'] == 'luebeck':
                    i_subject.append("Lübeck")
        for album in data['albums']:
            if album['title'] not in i_subject:
                i_subject.append(album['title'])

        print(">>>>>>>>>>>>>>")
        print(i_name)
        print(i_description)
        print(i_tags)
        print(i_creator)
        print(i_date)
        print(i_license)
        print(i_subject)
        i_license_url = ''
        if i_license == 'Attribution-NonCommercial License':
            i_license_url = 'https://creativecommons.org/licenses/by-nc/4.0/deed.de'
        if i_license == 'Public Domain Dedication (CC0)':
            i_license_url = 'https://creativecommons.org/publicdomain/zero/1.0/deed.de'
        if i_license == 'Attribution License':
            i_license_url = 'https://creativecommons.org/licenses/by/4.0/deed.de'
        if i_license == 'Attribution-NonCommercial-ShareAlike License':
            i_license_url = 'https://creativecommons.org/licenses/by-nc-sa/4.0/deed.de'
        if i_license == 'Public Domain Mark':
            i_license_url = 'https://creativecommons.org/publicdomain/zero/1.0/deed.de'

        # For some reason, the automated internet archive spam detection seems to not flag images as spam as much if
        # they have IMG_ in their name probably because that's what some cameras do, so it might be an actual photo
        # taken and not some AI generated spamming...
        if i_name.startswith('IMG'):
            i_name = 'PACK_ARCH_' + i_name[:60]
        else:
            i_name = 'PACK_ARCH_IMG_' + i_name[:56]

        # umlauts are giving us some bullshit s3 bucket exception that one has to figure out...
        i_name = i_name.replace('ü', 'u')
        i_name = i_name.replace('Ü', 'U')
        i_name = i_name.replace('ä', 'a')
        i_name = i_name.replace('Ä', 'A')
        i_name = i_name.replace('ö', 'o')
        i_name = i_name.replace('Ö', 'O')
        i_name = i_name.replace('ß', 's')
        i_name = i_name.replace('(', '')
        i_name = i_name.replace(')', '')
        i_name = i_name.replace(':', '')
        i_name = i_name.replace('-', '_')
        i_name = i_name.replace('.', '')
        i_name = i_name.replace(',', '')

        i_name = i_name + "_" + data['id']

        # md = {'collection': 'test_collection', 'title': i_name, 'description': i_description, 'mediatype': 'image',
        #      'creator': i_creator, 'publisher': 'StudentenPACK', 'date': i_date, 'licenseurl': i_license_url}
        # md = {'collection': 'Community image', 'title': i_name, 'description': i_description, 'mediatype': 'image',
        #     'creator': i_creator, 'publisher': 'StudentenPACK', 'date': i_date, 'licenseurl': i_license_url}

        md = {'collection': 'opensource_image', 'title': i_name, 'description': i_description, 'subject': i_subject,
              'mediatype': 'image', 'creator': i_creator, 'publisher': 'StudentenPACK', 'date': i_date,
              'licenseurl': i_license_url}

        try:
            actual_upload(i_name, image_file, md, access_key=access_key, secret_key=secret_key)
            shutil.move(image_file, "./done/" + image_file.split('/')[-1])
            errorcount = 0
        except Exception as error:
            errorcount = errorcount + 1
            print("Error " + image_file)
            print(error)
            print("Errorcount: "+str(errorcount))

        print("wait")
        # unclear how many seconds are needed to not run into rate limiting...
        # also, unclear of randomizing the duration helps at all...
        time.sleep(5)
        #r_sleep = random.randint(5, 10)
        #time.sleep(r_sleep)


errorcount = 0
prepare_directory()
upload_images()
# print(directory_of_images)
print(tags)
