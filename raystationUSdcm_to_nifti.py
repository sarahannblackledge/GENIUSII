import os
import numpy as np
import SimpleITK as sitk
import pydicom as dicom
import sys
sys.path.append('/Users/sblackledge/PycharmProjects/pythonProject/GENIUSII')
from copy_dicom_tags import copy_dicom_tags
from sitk_im_create_simple import sitk_im_create_simple

'''Writes US dicom exported from Raystation to compressed nifti file to user-specified location.
Details:
    US images are not saved in the dicom file format by default. To get them in this format, we must use RayStation as a
    middle-man. Specifically, we must register the US to the CTref in the Clarity workstation, export these registered 
    US images to RayStation. From Raystation, we export these US images to the bridge.
    
    NOTE: DON'T SELECT ALL DESIRED US FILES AND EXPORT IN ONE GO!! This will cause all of the files from different fractions
    to be lumped together in one folder, and the information about the scan date will be lost so we won't be able to match
    the US with the corresponding CBCT. Instead, export each US individually to it's own folder. Name this folder using the
    following convention: 'US_Jul01' (but obviously replace the date with the actual date of the fraction). 
    
    
Inputs:
    1. dcm_dir_us: full file path to the directory where the US dicoms have been saved (exported from RayStation)
    2. save_dir: full file path to the directory where you wish to save the nifti files. 
        i.e. save_dir = '/Users/sblackledge/Documents/GENIUSII_exports/nifti_dump/images/g01' 


Output:
    1. nii.gz file of CBCT that has been registered/resampled to the CTref.'''
def USdcm_to_nifti(dcm_dir_us, save_dir):
    us_sitk = sitk_im_create_simple('CT', dcm_dir_us) #Read in dicom files and generate sitk object

    #Extract sample dcm file
    # (ensure DSstore files, or other files not following naming convention of exported dicoms are removed)
    USfiles = os.listdir(dcm_dir_us)
    USfiles = [x for x in USfiles if 'CT' in x] #US files names have CT prefix even though they aren't CT images
    sample_us_fpath = os.path.join(dcm_dir_us, USfiles[0])
    sample_us_dcm = dicom.read_file(sample_us_fpath)

    copy_dicom_tags(us_sitk, sample_us_dcm, ignore_private=True)

    #Generate new filename: assume parent directory of US dicom has desired name (i.e. date of US image)
    USdate = os.path.basename(dcm_dir_us)
    fname = USdate + '.nii.gz'
    fpath_US_nifti = os.path.join(save_dir, fname)
    sitk.WriteImage(us_sitk, fpath_US_nifti, True)

save_dir = '/Users/sblackledge/Documents/GENIUSII_exports/nifti_dump/images/g01'
dcm_dir_us = '/Users/sblackledge/Documents/GENIUSII_exports/RayStation/g01/US_June20'
USdcm_to_nifti(dcm_dir_us, save_dir)