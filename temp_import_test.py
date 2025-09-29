import sys
sys.path.insert(0, 'C:/Users/Johannes/Nextcloud/BioDYM/bioDYM-CERT-edit-main/src')
sys.path.insert(0, 'C:/Users/Johannes/Nextcloud/BioDYM/bioDYM-CERT-edit-main/framework/ODYM-master_20241127/odym/modules')
try:
    import config
    import data_loader
    import system_setup
    from engine import solver
    import plotting
    print('BioDYM modules imported successfully')
except ImportError as e:
    print(f'Import error: {e}')
    print('   Current Python path:')
    for i, path in enumerate(sys.path[:5]):  # Show first 5 paths
        print(f'   {i}: {path}')
    raise