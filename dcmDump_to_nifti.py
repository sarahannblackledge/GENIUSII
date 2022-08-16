import os
import numpy as np
import SimpleITK as sitk
import pydicom as dicom
import sys
sys.path.append('/Users/sblackledge/PycharmProjects/pythonProject/GENIUSII')
from copy_dicom_tags import copy_dicom_tags

ct_directory = '/Users/sblackledge/Documents/GENIUSIII_exports/Clarity/g01/DICOMRawData'
study_uids_blacklist = {}
floc_el = 0x19100c #Used to store the file location in read dicoms

# Load in the ct dicoms
ct_dicoms = {}
for dicom_file in os.listdir(ct_directory):
    if dicom_file == ".DS_Store":
        continue

    try:
        dicom_path = os.path.join(ct_directory, dicom_file)
        dcm = dicom.read_file(dicom_path, stop_before_pixels=True)
        series_uid = dcm.SeriesInstanceUID
        if dcm.StudyInstanceUID in study_uids_blacklist.keys():
            break
        if not series_uid in ct_dicoms:
            ct_dicoms[series_uid] = []
        dcm.add_new(floc_el, "ST", dicom_path)
        ct_dicoms[series_uid].append(dcm)
    except:
        raise

    # Now organise by ascending slice location
    for series_uid in ct_dicoms:
        slice_locations = [float(dcm.ImagePositionPatient[-1]) for dcm in ct_dicoms[series_uid]]
        ct_dicoms[series_uid] = np.array(ct_dicoms[series_uid])[np.argsort(slice_locations)].tolist()

ref_ct_study = ct_dicoms[series_uid]
ct_image = sitk.ReadImage([dcm[floc_el].value for dcm in ref_ct_study])
copy_dicom_tags(ct_image, ref_ct_study[0], ignore_private=True)
study_path = '/Users/sblackledge/Desktop/test_conversion.nii'
sitk.WriteImage(ct_image, study_path, True)

