import numpy as np
import SimpleITK as sitk
import cv2 as cv
import matplotlib.pyplot as plt
import os

''' Converts user-specified nifti mask into border. Saves as separate nifti file with same name as mask, but in different
subdirectory.

inputs: 
    1. fpath_nii: str - full filepath to nifti file where mask is stored (output from Clarity_dcmDump_to_nifti.py)
    Example: fpath_nii = '/Users/sblackledge/Documents/GENIUSII_exports/nifti_dump/masks/g01/PTV45_1.nii'
    2. save_dir: str - full filepath to directory where border nifti file should be saved.
    Example: save_dir = '/Users/sblackledge/Documents/GENIUSII_exports/nifti_dump/contours/g01'.
     '''

def mask2border(fpath_nii, save_dir):
    orig_mask_sitk = sitk.ReadImage(fpath_nii)
    mask_array = sitk.GetArrayFromImage(orig_mask_sitk)
    im_dims = mask_array.shape

    #Preallocate 3D array
    contours_3D_ax = np.zeros(im_dims)

    #Populate array with contour version of mask (slice by slice - axial). Also find sup and inf- most slices
    for i in range(im_dims[0]):
        test_slice = mask_array[i,:, :]
        im, contours, hierarchy = cv.findContours(test_slice, cv.RETR_TREE, cv.CHAIN_APPROX_NONE)
        drawing = np.zeros((test_slice.shape))
        test2 = cv.drawContours(drawing, contours, -1, (255, 0, 0), 1)
        contours_3D_ax[i, :, :] = test2

    #Save border-only mask as nifti
    fname = os.path.split(fpath_nii)[1]
    contour_im = sitk.GetImageFromArray(contours_3D_ax)
    contour_im.CopyInformation(orig_mask_sitk)
    savepath = os.path.join(save_dir, fname)
    sitk.WriteImage(contour_im, savepath, True)

''' Loops through all user-specified masks for an individual patient to create border versions for visualisation in ITK-SNAP.
inputs:
    1. structure_list: list of strings: list indicating what masks to convert to borders
        Example: structure_list = ['Bladder', 'CTV-T HRinit', 'CTV-T LRinit_1_Full', 'PTV45_1', 'PTV45_2', 'PTV45_3', 'PTV45_Robust', 'Rectum']
    2. patient_name: str - name of patient. Should correspond to name of sub-directory in 'masks' directory. Example: patient_name = 'g01'
    3. save_dir: str- full path to directory where border nifti files should be saved.
        Example: save_dir = save_dir = '/Users/sblackledge/Documents/GENIUSII_exports/nifti_dump/contours'
    4. source_dir: str - full path to directory where mask nifti files have been saved (output from dcmDump_to_nifti).
        Example: source_dir ='/Users/sblackledge/Documents/GENIUSII_exports/nifti_dump/masks'
        '''

def convert_selected_masks_to_borders(structure_list, patient_name, save_dir, source_dir):
    patient_dir = os.path.join(save_dir, patient_name)
    for i in structure_list:
        fname = i + '.nii'
        fpath_nii = os.path.join(source_dir, patient_name, fname)
        mask2border(fpath_nii, patient_dir)


structure_list = ['Bladder', 'CTV-T HRinit', 'CTV-T LRinit_1_Full', 'PTV45_1', 'PTV45_2', 'PTV45_3', 'PTV45_Robust', 'Rectum']
patient_name = 'g01'
save_dir = '/Users/sblackledge/Documents/GENIUSII_exports/nifti_dump/contours'
source_dir = '/Users/sblackledge/Documents/GENIUSII_exports/nifti_dump/masks'

convert_selected_masks_to_borders(structure_list, patient_name, save_dir, source_dir)
