## Back_up_project.py
## Description
## Backsup the tenant data from one cite and 
## transfer to other and builds the tenant

## Requirements:
## 1. Need to copy the public key into the remote host
## 2. Tenant should not exist in the remote host with same name
##      which is passed to backup script
## 3. No need to run the rebuild script in the remote host
##      this script wil take care
## 4. Make sure remote host is reachable and can ssh without a 
##      password
## How to run:
##    python Back_up_project.py -t <tenant name> -i <remote undercloud ip> -u <username> -p <password>
## Example: python Back_up_project.py -t ukumar -i 10.10.0.0 -u admin -p password

 
import sys
import subprocess
import os
import re
import time
import paramiko
import sys, getopt

# This module is used for the backing up the user data for the tenant
def users_backup(tenant, tenant_id):
    command_to_execute = "keystone user-list --tenant-id " + tenant_id + " | tail -n +4 | head -n -1 | cut -d '|' -f 3,5 >> ./" + tenant + "_backup/" + tenant + ".userlist"
    obj_output = subprocess.Popen(command_to_execute, stdout=subprocess.PIPE, shell=True)
    (output, err) = obj_output.communicate()

# internal_networks is used to back up the networks that belong to tenant
def internal_networks(tenant, tenant_id):
    command_to_execute = "neutron net-list --tenant_id " + tenant_id + " | grep -v + | tail -n +2 | cut -d '|' -f 3,4"
    obj_output = subprocess.Popen(command_to_execute, stdout=subprocess.PIPE, shell=True)
    (output, err) = obj_output.communicate()
    if output:
        output_list = output.split("\n")
        output_list.pop(-1)
        # for list of networks for the tenant is backed up in to networks.txt
        for line in output_list:
            new_list = line.split(" | ")
            cidr = new_list[1].split(" ")
            new_cidr = new_list[0] + " " + cidr[1]
            command_to_execute = "echo " + new_cidr + " >> ./" + tenant + "_backup/" + "networks.txt"
            obj_output = subprocess.Popen(command_to_execute, stdout=subprocess.PIPE, shell=True)
            (output, err) = obj_output.communicate()

# security_grps backups all the rules that belong to that particular tenant
def security_grps(tenant, tenant_id):
    command_to_execute = "neutron security-group-list --tenant-id " + tenant_id + " | grep -v + | tail -n +2 | cut -d '|' -f 2 | sed '/^\s*$/d'"
    obj_output = subprocess.Popen(command_to_execute, stdout=subprocess.PIPE, shell=True)
    (output, err) = obj_output.communicate()
    raw_secgrp_list = output.split('\n')
    raw_secgrp_list.pop(-1)
    # Gets the list of security group and back up into secgrps folder
    for secgrp_id in raw_secgrp_list:
        command_to_execute = "neutron security-group-show " + secgrp_id + "  | tail -n +6 | head -1 | cut -d '|' -f 3| sed '/^\s*$/d'"
        obj_output = subprocess.Popen(command_to_execute, stdout=subprocess.PIPE, shell=True)
        (output, err) = obj_output.communicate()
        secgrp_name = output.strip()
        command_to_execute = "neutron security-group-show " + secgrp_id + " >> ./" + tenant + "_backup/secgrps/" +  secgrp_name
        obj_output = subprocess.Popen(command_to_execute, stdout=subprocess.PIPE, shell=True)
        (output, err) = obj_output.communicate()

# Below module bcakups the quota information of that tenant
def quota_backup(tenant, tenant_id):
    # backs up the nova quota for the tenant
    command_to_execute = "nova quota-show  --tenant " + tenant_id + " >> ./" + tenant + "_backup/" + tenant + ".nova_quota_show"
    obj_output = subprocess.Popen(command_to_execute, stdout=subprocess.PIPE, shell=True)    
    (output, err) = obj_output.communicate()
    # gets the cinder qouta for the tenant
    command_to_execute = "cinder quota-show " + tenant_id + " >> ./"  + tenant + "_backup/" + tenant + ".nova_quota_show"
    obj_output = subprocess.Popen(command_to_execute, stdout=subprocess.PIPE, shell=True)
    (output, err) = obj_output.communicate()

# Gets the image information and downloads the image into backup folder
def image_backup(tenant, tenant_id):
    # Gets the image list and puts the list into the image_list file
    command_to_execute = "glance image-list --owner=" + tenant_id + " | tail -n +4 | head -n -1 >> ./" + tenant + "_backup/image_list"
    obj_output = subprocess.Popen(command_to_execute, stdout=subprocess.PIPE, shell=True)
    (output, err) = obj_output.communicate()

    # Gets the image list and will download each image into backup folder
    command_to_execute = "glance image-list --owner=" + tenant_id + " | awk '{print $2, $3, $4}' | tail -n +4 | head -n -1"
    obj_output = subprocess.Popen(command_to_execute, stdout=subprocess.PIPE, shell=True)
    (output, err) = obj_output.communicate() 
    image_list = output.split("\n")
    image_list.pop()

    if image_list:
        command_to_execute = "cd ./" + tenant + "_backup"
        obj_output = subprocess.Popen(command_to_execute, stdout=subprocess.PIPE, shell=True)
        (output, err) = obj_output.communicate()
        for image in image_list:
            image_info = image.split("|")
            command_to_execute = "glance image-download --file ./" + tenant + "_backup/" + image_info[1].strip() + " --progress " + image_info[0].strip()
            obj_output = subprocess.Popen(command_to_execute, stdout=subprocess.PIPE, shell=True)
            (output, err) = obj_output.communicate()        

# Backups all the flavors that belongs to the tenant
def flavor_backup(tenant, tenant_id):
    # gets the flavor list for the tenant
    command = "nova flavor-list --all | awk '{print $4}' | tail -n +4 | head -n -1"
    obj_output = subprocess.Popen(command, stdout=subprocess.PIPE, shell=True)
    (output, err) = obj_output.communicate()
    flavors_list = output.split('\n')

    # gets the each flavor and saves that data flavor folder
    for flavor in flavors_list:
        command = "nova flavor-access-list --flavor " + flavor + " | awk '{print $2,$3,$4}' | tail -n +4 | head -n -1"
        obj_output = subprocess.Popen(command, stdout=subprocess.PIPE, shell=True)
        (output, err) = obj_output.communicate()
        tenant_list = output.split('\n')
        tenant_list.pop()
        
        for tenant_id_get in tenant_list:
            list_detail = tenant_id_get.split("|")
            if list_detail[1]:
                if list_detail[1].strip() == tenant_id:
                    command = "nova flavor-show " + list_detail[0].strip() + " >> ./"+  tenant + "_backup/" + "flavors/" + list_detail[0].strip()
                    obj_output = subprocess.Popen(command, stdout=subprocess.PIPE, shell=True)
                    (output, err) = obj_output.communicate()

# Volume Backup is used to convert the volumes into images and makes a backup
# With the older version cinder api this module is not supported on this
# platform please check back after the cinder api update
def volume_backup(tenant, tenant_id):
    command = "cinder list --all-tenants | grep " + tenant_id
    obj_output = subprocess.Popen(command, stdout=subprocess.PIPE, shell=True)
    (output, err) = obj_output.communicate()
    volume_list = output.split('\n')
    volume_list.pop()

    for volume in volume_list:
        volume_details = volume.split('|')
        if volume_details[3].strip() == "in-use":
            command = "cinder show " + volume_details[1].strip()
            obj_output = subprocess.Popen(command, stdout=subprocess.PIPE, shell=True)
            (output, err) = obj_output.communicate()
            details = output.split("|")
            details =  details[5].split(" ")
            id_instance = details[2][2:][:-2]
            command = "nova stop " + id_instance
            obj_output = subprocess.Popen(command, stdout=subprocess.PIPE, shell=True)
            time.sleep(10)
            command = "nova show " + id_instance
            obj_output = subprocess.Popen(command, stdout=subprocess.PIPE, shell=True)
            (output, err) = obj_output.communicate()
            if ("Attempt to boot from volume - no image supplied" in output and "os-extended-volumes:volumes_attached | [{\"id\":" in output):
                comment = "As this is a boot volume for the running instance we are unable to take the backup of this volume"
                description = "Unable to take a snapshot of instance and even for the volume as unable to convert it into a image and download it"
                print comment
                print description
                #create a snapshot of the instance
                time.sleep(10)
                command = "nova show " + id_instance + " >> /root/volumes/" + id_instance + "_nova_show" 
                obj_output = subprocess.Popen(command, stdout=subprocess.PIPE, shell=True)
                command = "nova image-create " + id_instance + " " + id_instance + "_instance_snaphot"
                obj_output = subprocess.Popen(command, stdout=subprocess.PIPE, shell=True)
                time.sleep(10)
                command = "glance image-list | grep " + id_instance + "_instance_snaphot | cut -d '|' -f 2"
                obj_output = subprocess.Popen(command, stdout=subprocess.PIPE, shell=True)
                (output, err) = obj_output.communicate()
                command = "glance image-download --file /root/volumes/" + volume_details[4].strip() +  ".qcow --progress " + output.strip()
                obj_output = subprocess.Popen(command, stdout=subprocess.PIPE, shell=True)
            elif "os-extended-volumes:volumes_attached | [{\"id\":" in output:
                command = "nova volume-detach " + id_instance + " " + volume_details[1].strip()
                obj_output = subprocess.Popen(command, stdout=subprocess.PIPE, shell=True)
                time.sleep(10)
                upload_to_image(volume_details, tenant, tenant_id)
            else:
                upload_to_image(volume_details, tenant, tenant_id)
        else:
            upload_to_image(volume_details, tenant, tenant_id)

# Thia module is used by volume backup in order to convert the volumes  to images
# and can be downloaded in to the backup folder             
def upload_to_image(volume_details, tenant, tenant_id):
    print volume_details
    command = "cinder upload-to-image --disk-format qcow2 --container-format bare " + volume_details[1].strip() + " " + volume_details[5].strip()
    print command
    obj_output = subprocess.Popen(command, stdout=subprocess.PIPE, shell=True)
    (output, err) = obj_output.communicate()
    image_details = output.split("|")
    print image_details
    command = "cinder show " + volume_details[1].strip() + " >> ./" + tenant + "_backup/volumes/" + volume_details[4].strip() + "_image_show"
    obj_output = subprocess.Popen(command, stdout=subprocess.PIPE, shell=True)
    time.sleep(10)
    command = "glance image-download --file ./" + tenant + "_backup/volumes/" + image_details[20].strip() + ".qcow " + image_details[17].strip()
    obj_output = subprocess.Popen(command, stdout=subprocess.PIPE, shell=True)
    (output, err) = obj_output.communicate()

# This module retrives the command line arguments and sends to variables respectively
def arguments(argv):
   inputfile = ''
   outputfile = ''
   try:
      opts, args = getopt.getopt(argv,"ht:i:u:p:",["tenant-name=","remote-ip=", "username=", "password="])
   except getopt.GetoptError:
      print 'Back_up_project.py -t <tenant name> -i <remote ip>'
      sys.exit(2)
   for opt, arg in opts:
      if opt == '-h':
         print 'Back_up_project.py -t <tenant name> -i <remote ip> -u <username> -p <password>'
         sys.exit()
      elif opt in ("-t", "--tenant-name"):
         inputfile = arg
      elif opt in ("-i", "--remote-ip"):
         outputfile = arg
      elif opt in ("-u", "--username"):
         user = arg
      elif opt in ("-p", "--password"):
         passwd = arg
   return inputfile, outputfile, user, passwd 

if __name__ == '__main__':
  
    # Gets the tenant & remote ip from the command line 
    # using the arguments module above
    tenant_name, remote_ip, user_name, passwd = arguments(sys.argv[1:])
    # Below steps are used to ssh and maintain the session
    # with the remotw ip
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(remote_ip, username=user_name, password=passwd)
    command_to_execute = "source /home/stack/overstackrc"
    ssh.exec_command(command_to_execute)
    
    #Based on the passed tenant name getting the tenant id
    command_to_execute = "mkdir " + tenant_name + "_backup; cd " + tenant_name + "_backup; mkdir secgrps flavors volumes"
    obj_output = subprocess.Popen(command_to_execute, stdout=subprocess.PIPE, shell=True)
    (output, err) = obj_output.communicate()

    command_to_execute = "keystone tenant-list | grep " + tenant_name + " | cut -d '|' -f 2"
    obj_output = subprocess.Popen(command_to_execute, stdout=subprocess.PIPE, shell=True)
    (output, err) = obj_output.communicate()
    tenant_id = output.strip()
    time.sleep(1)

    # Below are the modules that used for different taska
    # perform the specific task and save to the backup folder
    users_backup(tenant_name, tenant_id)
    internal_networks(tenant_name, tenant_id)
    security_grps(tenant_name, tenant_id)
    quota_backup(tenant_name, tenant_id)
    image_backup(tenant_name, tenant_id)
    flavor_backup(tenant_name, tenant_id)
    # Please use volume backup when the cinder api's are updated
    #volume_backup(tenant_name, tenant_id)
  
    # Then the backup folder is compressed and transfered to
    # remote system
    time.sleep(1)
    command_to_execute = "tar -czvf " + tenant_name + "_backup.tar.gz Rebuild_project.py " + tenant_name + "_backup"
    obj_output = subprocess.Popen(command_to_execute, stdout=subprocess.PIPE, shell=True)
    command_to_execute = "scp -r /home/stack/osp_backup/"+ tenant_name + "_backup.tar.gz " + "stack@" + remote_ip +":/home/stack/osp_backup/"
    obj_output = subprocess.Popen(command_to_execute, stdout=subprocess.PIPE, shell=True)

    # After the transfer files are uncompressed and will run
    # rebuild script
    time.sleep(5)
    command_to_execute = "tar -zxvf /home/stack/osp_backup/" + tenant_name + "_backup.tar.gz -C /home/stack/osp_backup/"
    ssh.exec_command(command_to_execute)
    time.sleep(2)
    command_to_execute = "ssh stack@" + remote_ip + " \"source /home/stack/overcloudrc; python /home/stack/osp_backup/Rebuild_project.py " + tenant_name + "\" >>  /home/stack/osp_backup/rebuild_log.txt"
    obj_output = subprocess.Popen(command_to_execute, stdout=subprocess.PIPE, shell=True)
    (output, err) = obj_output.communicate()
    ssh.close()
