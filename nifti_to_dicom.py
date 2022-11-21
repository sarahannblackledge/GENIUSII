import pydicom
import SimpleITK as sitk
import os
from pydicom.uid import generate_uid
import datetime
import numpy as np

''' rescales array so values lie between range specified in 'out_range'. Also returns slope and intercept used 
for conversion.
Inputs:
    1. rescaled_arr: numpy array
    2. out_range: list of length two indicating desired max and min values of rescaled array
        example: out_range = [0, 65535]'''

def rescale_array(arr, out_range):
    orig_min = np.amin(arr) #x2
    orig_max = np.amax(arr) #x1
    y2 = out_range[0]  #min of uint16
    y1 = out_range[1] #max of uint16

    m = (y2-y1)/(orig_min-orig_max)
    b = m*(0-orig_max) + y1

    rescaled_arr = m*(arr - orig_min) + y2

    return rescaled_arr, m, b, orig_max, orig_min

'''Converts specified slice(index) of 3D numpy array into dicom file (2D slice)
Inputs:
    1. rescaled_arr: nxmxd numpy array that has been rescaled so values lie between 0 and 4095 (uint12)
    2. m: slope applied in linear transformation from original array to rescaled array (inverse taken in code)
    3. b: intersection applied in linear transformation from rescaled array to original array 
    4. ipp: image position patient (3xn) value (physical coordinate of top left pixel)
    5. pix_spacing (3xn): pixel spacing (mm) of voxel
    6. series_id: unique SOP identifier
    7. save_dir: full filepath where you wish dicom to be saved.
    8. index: slice number of 3D array to be saved
    9. fpath_template: full filepath of template dicome file whose tags will be overwritten and re-saved as new dcm
    
Output: dicom files labeled "sliceXXX.dcm" in user-specified directory'''

def convertNsave(rescaled_arr, m, b, ipp, pix_spacing, series_id, save_dir, index, fpath_template):

    #Generate new uid
    new_SOP_id = generate_uid()

    #Read in template dicom file
    dicom_file = pydicom.dcmread(fpath_template)

    #Update time and date info with current datetime
    dt = datetime.datetime.now()
    timeStr = dt.strftime('%H%M%S.%f')  # long format with micro seconds
    dateStr = dt.strftime('%Y%m%d')
    dicom_file.InstanceCreationTime = timeStr
    dicom_file.InstanceCreationDate = dateStr
    dicom_file.StudyDate = dateStr
    dicom_file.SeriesDate = dateStr
    dicom_file.AcquisitionDate = dateStr
    dicom_file.ContentDate = dateStr

    #Update SOPInstanceUID (each slice) and SeriesInstanceUID (constant for all slices in series)
    dicom_file.SOPInstanceUID = new_SOP_id
    dicom_file.SeriesInstanceUID = series_id

   #Update pixel data
    rescaled_arr = rescaled_arr.astype('uint16')
    dicom_file.RescaleSlope = 1/m
    dicom_file.RescaleIntercept = b
    dicom_file.PixelData = rescaled_arr.tobytes()

    #Update image dimensions
    dicom_file.Rows = rescaled_arr.shape[0]
    dicom_file.Columns = rescaled_arr.shape[1]

    #Update spatial information and voxel size
    dicom_file.ImagePositionPatient[0] = ipp[0]
    dicom_file.ImagePositionPatient[1] = ipp[1]
    dicom_file.ImagePositionPatient[2] = ipp[2]
    dicom_file.SliceLocation = ipp[2]
    dicom_file.PixelSpacing[0] = pix_spacing[0]
    dicom_file.PixelSpacing[1] = pix_spacing[1]
    dicom_file.SliceThickness = pix_spacing[2]

    #Update instance number
    dicom_file.InstanceNumber = index + 1

    dicom_file.save_as(os.path.join(save_dir, f'slice{index}.dcm'))

'''Generates dicom file for every slice in nifti file
inputs:
    1. fpath_nifit_compound: full filename of nifti file that you wish to convert to dicom
    2. save_dir: full filepath of directory where you wish to save dicom files
    3. fpath_template: full filename of template dicom file (i.e. original dicom export of single US)'''

def nifti_to_dicoms(fpath_nifti_compound, save_dir, fpath_template):

    im_sitk = sitk.ReadImage(fpath_nifti_compound)
    im_arr = sitk.GetArrayFromImage(im_sitk)
    series_id = generate_uid()
    pix_spacing = im_sitk.GetSpacing()
    out_range = [0, 4095]
    rescaled_arr, m, btrash, orig_max, orig_min = rescale_array(im_arr, out_range)
    orig_arr, mtrash, b, new_max, new_min = rescale_array(rescaled_arr, [orig_min, orig_max])
    b = np.round(b)

    for i in range(rescaled_arr.shape[0]):
        arr = rescaled_arr[i, :, :]
        ipp = im_sitk.TransformIndexToPhysicalPoint((0, 0, i))
        convertNsave(arr, m, b, ipp, pix_spacing, series_id, save_dir, i, fpath_template)


fpath_template = '/Users/sblackledge/Documents/GENIUSII_exports/RayStation/g02/July_25_1447/CT1.2.826.0.1.3680043.2.1181.1.4.273440548174504.1666686875.0.dcm'

'''START EDIT'''
save_dir = '/Users/sblackledge/Documents/GENIUSII_exports/compound_dicoms/g01/June17'
fpath_nifti_compound = '/Users/sblackledge/Documents/GENIUSII_exports/nifti_dump/compound_images/g01/June17_compound.nii.gz'
'''END EDIT'''


nifti_to_dicoms(fpath_nifti_compound, save_dir, fpath_template)
