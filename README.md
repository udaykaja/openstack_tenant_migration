# openstack_tenant_migration
Requirements:
1. Need to copy the public key into the remote host
2. Tenant should not exist in the remote host with same name which is passed to backup script
3. No need to run the rebuild script in the remote host this script wil take care
4. Make sure remote host is reachable and can ssh without a  password

# How to run:
#    python Back_up_project.py -t <tenant name> -i <remote undercloud ip> -u <username> -p <password>
# Example: python Back_up_project.py -t ukumar -i 10.10.0.0 -u admin -p password
