import os
import numpy as np
import SimpleITK as sitk
import pydicom as dicom
import sys

sys.path.append('/Users/sblackledge/PycharmProjects/pythonProject/GENIUSII')
from copy_dicom_tags import copy_dicom_tags
from create_rtstruct_mask_SB import create_rtstruct_masks
from utils_RayStation import transformation_from_reg_dcm, get_date_name

'''Organizes CT and CBCT images exported from RayStation based on Series Instance UID. 
Saves as nifti files to user-specified directory. 

Notes: 
1. This only works on CT and CBCT data. Unfortunately it is impossible to sort through any US data exported in bulk
as the dates are not retained in the metadata upon transfer from Clarity to RayStation.
2. When you export from RayStation, be sure to anonymize, but tick the relevant boxes so that UIDs and study dates are
 retained.

Inputs:
    1. ct_directory: str - full filepath where data exported from RayStation are stored. This contains a dump of 
    all CBCT, CT, RTSTRUCT, and REG dicoms, and is not organized in an intuitive way.
    Example: ct_directory =  '/Users/sblackledge/Documents/GENIUSII_exports/RayStation/g02/Raystation_CTdump'
    2. save_dir: str - full filepath where nifti files should be saved. 
    Example: save_dir = '/Users/sblackledge/Documents/GENIUSII_exports/nifti_dump'
    3. patient_name: str - string indicating name of patient. Example: 'g02'
    4. masks_of_interest: list of strings: exact names of masks that should be exported and saved as niftis.
        example: masks_of_interest = ['Bladder', 'PTV45_1', 'PTV45_2', 'PTV45_3', 'PTV45_Robust', 'Rectum', 'CTV-E', 'CTV-T HRinit', 'CTV-T LRinit_1_Full']

Output:
    Nifti file for every (1) dcm image dataset and (2) relevant structure from the RTSTRUCT.dcm file exported from RayStation
    Note: no date or name information is stored in the metadata of these nifti files, so they are considered fully anonymized.
    HOWEVER, the nifti filename contains teh study date by default. I recommend changing this manually retrospectively once
    all desired data has been converted to nifti format (e.g. Fraction1.nii.gz).
'''


def DICOMRawData_to_nifti(ct_directory, save_dir, patient_name, masks_of_interest):
    study_uids_blacklist = {}
    floc_el = 0x19100c  # Used to store the file location in read dicoms

    # Create 'images' sub-directory.
    im_dir = os.path.join(save_dir, 'images', patient_name)
    CHECK_FOLDER = os.path.isdir(im_dir)
    if not CHECK_FOLDER:
        os.makedirs(im_dir)

    # Create 'masks' sub-directory
    mask_dir = os.path.join(save_dir, 'masks', patient_name)
    CHECK_FOLDER = os.path.isdir(mask_dir)
    if not CHECK_FOLDER:
        os.makedirs(mask_dir)

    # Load in the ct dicoms and RTSTRUCT dicoms as separate lists
    ct_dicoms = {}
    reg_dicoms = []

    for dicom_file in os.listdir(ct_directory):
        if dicom_file == ".DS_Store":
            continue

        try:
            dicom_path = os.path.join(ct_directory, dicom_file)
            dcm = dicom.read_file(dicom_path, stop_before_pixels=True)
            series_uid = dcm.SeriesInstanceUID
            modality = dcm.Modality
            if dcm.StudyInstanceUID in study_uids_blacklist.keys():
                break

            # Both CT and CBCT labeled with modality 'CT'
            if modality == 'CT':
                if not series_uid in ct_dicoms:
                    ct_dicoms[series_uid] = []
                dcm.add_new(floc_el, "ST", dicom_path)
                ct_dicoms[series_uid].append(dcm)

            if modality == 'RTSTRUCT': #Should only be one RS file in directory.
                ref_rtstruct = dicom.read_file(dicom_path, stop_before_pixels=True)
                ref_rtstruct.add_new(floc_el, "ST", dicom_path)
                ref_rtstruct_uid = ref_rtstruct.SOPInstanceUID

            if modality == 'REG':
                reg_dcm = dicom.read_file(dicom_path, stop_before_pixels=True)
                reg_dcm.add_new(floc_el, "ST", dicom_path)
                reg_dicoms.append(reg_dcm)

        except:
            raise

    # Now organise files in CT lists by ascending slice location
    for series_uid in ct_dicoms:
        slice_locations = [float(dcm.ImagePositionPatient[-1]) for dcm in ct_dicoms[series_uid]]
        ct_dicoms[series_uid] = np.array(ct_dicoms[series_uid])[np.argsort(slice_locations)].tolist()

    # Find the CT image corresponding to the RTSTRUCT and save to nifti
    ref_ct_series_uid = ref_rtstruct[0x3006, 0x10][0][0x3006, 0x12][0][0x3006, 0x14][0][0x20, 0xe].value
    for series_uid in ct_dicoms:
        if series_uid == ref_ct_series_uid:
            ref_ct_study = ct_dicoms[series_uid]
            study_date = ref_ct_study[0].ContentDate #extract date from first file
            ref_ct_image = sitk.ReadImage([dcm[floc_el].value for dcm in ref_ct_study])  # sitk object for ref CT
            copy_dicom_tags(ref_ct_image, ref_ct_study[0], ignore_private=True)
            ref_ct_image.SetMetaData('0008,0020', study_date)
            ref_ct_image.SetMetaData('0008,103e', 'CT')

            fname = get_date_name(ref_ct_image)

            # Save CT to images sub-directory in 'nifti dump' folder
            save_path = os.path.join(im_dir, fname)
            sitk.WriteImage(ref_ct_image, save_path, True)

            if ref_ct_study is None:
                print("Could not find a CT series corresponding to RTSTRUCT: %s" % str(ref_rtstruct_uid))
                continue

    #Find CBCT corresponding to REG files, generated resampled CBCT (to match ref CT), and save as nifti
    for reg_dicom in reg_dicoms:
        ref_ID = reg_dicom.ReferencedSeriesSequence[-1].SeriesInstanceUID
        for series_uid in ct_dicoms:
            if series_uid == ref_ID:
                test = ct_dicoms[series_uid]
                CBCT_image = sitk.ReadImage([dcm[floc_el].value for dcm in test]) #sitk object for CBCT
                study_date = test[0].ContentDate
                r, offset = transformation_from_reg_dcm(reg_dicom)

                # Apply transformation and resampling to CBCT image to register to CT image
                affine = sitk.AffineTransform(3)
                affine.SetMatrix(r)
                affine.SetTranslation(offset)
                CBCT_resample = sitk.Resample(CBCT_image, ref_ct_image, affine, sitk.sitkLinear, -1024, sitk.sitkFloat32)
                copy_dicom_tags(CBCT_resample, ref_ct_study[0], ignore_private=True)
                CBCT_resample.SetMetaData('0008,0020', study_date)
                CBCT_resample.SetMetaData('0008,103e', 'CBCT')

                fname = get_date_name(CBCT_resample)

                # Save CBCTs to images sub-directory in 'nifti dump' folder
                save_path = os.path.join(im_dir, fname)
                sitk.WriteImage(CBCT_resample, save_path, True)

    # Generate masks of each structure in RTSTRUCT.
    rtstruct_images_sub = create_rtstruct_masks(ref_rtstruct, ref_ct_image, masks_of_interest)  # output: list of sitk objects

    for im in rtstruct_images_sub:
        structure_name = im.GetMetaData("ContourName") + '.nii.gz'
        fpath_structure = os.path.join(mask_dir, structure_name)
        sitk.WriteImage(im, fpath_structure, True)

    return ct_dicoms, ref_ct_image, rtstruct_images_sub

masks_of_interest = ['Bladder', 'PTV45_1', 'PTV45_2', 'PTV45_3', 'PTV45_Robust', 'Rectum', 'CTV-E', 'CTV-T HRinit', 'CTV-T LRinit_1_Full']
patient_name = 'g02'
ct_directory = '/Users/sblackledge/Documents/GENIUSII_exports/RayStation/g02/RayStation_CTdump'
save_dir = '/Users/sblackledge/Documents/GENIUSII_exports/nifti_dump'
ct_dicoms, ct_example, rtstruct_sitk = DICOMRawData_to_nifti(ct_directory, save_dir, patient_name, masks_of_interest)

