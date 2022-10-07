import pydicom as dicom
import SimpleITK as sitk
import matplotlib.pyplot as plt
import numpy as np
from numpy import linalg
import sys
import os
sys.path.append('/Users/sblackledge/PycharmProjects/pythonProject/GENIUSII')
from copy_dicom_tags import copy_dicom_tags

'''Registers CBCT to CTref and writes to compressed nifti file to user-specified location.
Details:
    In cases where 'Option 3' was not selected or not available at XVI export, you will need to import the daily CBCTs
    into clinical RayStation using the 'Import XVI' script to retain the CBCT-CT registration that was performed at 
    treatment. When these CBCTs are exported from RayStation, the registration is saved as a 'REG.dcm' file rather than 
    being inherently incorporated into the CBCT image dicom files. This code applies the registration contained in the 
    REG.dcm file to the corresponding CBCTs and saves the output as a compressed nifti.
    
Inputs:
    1. CT_dir: full file path to the ref CT directory (exported from RayStation)
    2. CBCT_dir: full file path to the CBCT directory (contains CT.dcm files and corresponding REG.dcm file).
        NOTE: export each CBCT+reg into a separate file named with the modality and date (i.e. 'CBCT_Jun29). Don't select
        all desired files and export in one go, otherwise everything will be mixed in one directory
    3. save_dir: full file path to the directory where you wish to save the nifti files. 
        i.e. save_dir = '/Users/sblackledge/Documents/GENIUSII_exports/nifti_dump/images/g01' 
        
        
Output:
    1. nii.gz file of CBCT that has been registered/resampled to the CTref.'''

def CBCTdcm_to_nifti(CT_dir, CBCT_dir, save_dir):
    # Make sitk CT image (reference)
    files_CT = np.array([os.path.join(CT_dir, fl) for fl in os.listdir(CT_dir) if "dcm" in fl and "CT" in fl])
    dicoms = np.array([dicom.read_file(fl, stop_before_pixels = True) for fl in files_CT])
    locations = np.array([float(dcm.ImagePositionPatient[-1]) for dcm in dicoms])
    files_CT = files_CT[np.argsort(locations)]
    CT = sitk.ReadImage(files_CT)


    # Make sitk CBCT image (moving)
    files_CBCT = np.array([os.path.join(CBCT_dir, fl) for fl in os.listdir(CBCT_dir) if "dcm" in fl and "CT" in fl])
    dicoms = np.array([dicom.read_file(fl, stop_before_pixels = True) for fl in files_CBCT])
    locations = np.array([float(dcm.ImagePositionPatient[-1]) for dcm in dicoms])
    files_CBCT = files_CBCT[np.argsort(locations)]
    CBCT = sitk.ReadImage(files_CBCT)


    # Get transformation matrix from reg file. Assume reg file in same directory as CBCT dcm files
    reg_file = np.array([os.path.join(CBCT_dir, fl) for fl in os.listdir(CBCT_dir) if "dcm" in fl and "REG" in fl])
    fpath = reg_file[0]

    reg_dicom = dicom.read_file(fpath)
    RegistrationSequence = reg_dicom.RegistrationSequence
    Item_2 = RegistrationSequence[1]
    MatrixRegistrationSequence = Item_2.MatrixRegistrationSequence
    Item_1_1 = MatrixRegistrationSequence[0]
    MatrixSequence = Item_1_1.MatrixSequence
    Item_1_2 = MatrixSequence[0]
    T = Item_1_2.FrameOfReferenceTransformationMatrix
    T = np.asarray(T)
    TM = np.reshape(T, (4,4))
    TM = linalg.inv(TM)

    # Get 3x3 rotation sub-matrix
    Mr = TM[0:3, 0:3]
    r = Mr.ravel()

    # Get offset
    offset = TM[0:3,3]

    # Apply transformation and resampling to CBCT image to register to CT image
    affine = sitk.AffineTransform(3)
    affine.SetMatrix(r)
    affine.SetTranslation(offset)
    CBCT_resample = sitk.Resample(CBCT, CT, affine, sitk.sitkLinear, -1024, sitk.sitkFloat32)

    #Generate name and path for saving compressed nifti. Assume source directory is named with modality and date (i.e. 'CBCT_Jun29')
    fname = (os.path.split(CBCT_dir))[1] + '.nii.gz'
    save_path = os.path.join(save_dir, fname)

    #Generate sample CT dicom for the purpose of copying the metadata
    sample_ct_dcm = dicom.read_file(files_CT[0], stop_before_pixels = True)
    copy_dicom_tags(CBCT_resample, sample_ct_dcm, ignore_private=True)

    #Write registered CBCT to nifti
    sitk.WriteImage(CBCT_resample, save_path, True)

CT_dir = "/Users/sblackledge/Documents/GENIUSII_exports/RayStation/g01/CT_full"
CBCT_dir = "/Users/sblackledge/Documents/GENIUSII_exports/RayStation/g01/CBCT_Jul01"
save_dir = '/Users/sblackledge/Documents/GENIUSII_exports/nifti_dump/images/g01'

CBCTdcm_to_nifti(CT_dir, CBCT_dir, save_dir)



#Display
'''fig1 = plt.figure(1)
plt.title('CT')
CT_im = sitk.GetArrayFromImage(CT)
plt.imshow(CT_im[134], cmap = 'gray')
plt.show()

fig2 = plt.figure(2)
plt.title('CBCT')
CBCT_im = sitk.GetArrayFromImage(CBCT)
plt.imshow(CBCT_im[134], cmap = 'gray')
plt.show()

fig3 = plt.figure(3)
plt.title('Resampled CBCT')
CBCT_Resampled = sitk.GetArrayFromImage(CBCT_resample)
plt.imshow(CBCT_Resampled[134], cmap = 'gray')
plt.show()'''

# =============================================================================
#
# #Display
# dose_resample_arr = sitk.GetArrayFromImage(dose_resample)
# mri_arr = sitk.GetArrayFromImage(mri)
#
# max_slice = np.where(dose_resample_arr == np.max(dose_resample_arr))[0][0]
# max_dose = np.max(dose_resample_arr)
# print(max_dose)
# pl.imshow(mri_arr[max_slice], cmap = 'gray')
# pl.contour(dose_resample_arr[max_slice], np.array([0.2, 0.4, 0.6, 0.8]) * max_dose, colors = ['g', 'y', 'm', 'r'])
# pl.show()
# print(np.max(dose_resample_arr))
#
# =============================================================================
