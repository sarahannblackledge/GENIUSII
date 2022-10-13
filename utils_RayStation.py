import numpy as np
from numpy import linalg

''' Extracts transformation matrix (split into 3x3 rotations submatrix and offset components)
from REG.dcm files

inputs:
    1. reg_dicom: pydicom object returned after reading REG.dcm file.
    e.g. reg_dcm = dicom.read_file(dicom_path, stop_before_pixels=True)
outputs:
    1. r: 3.3 rotation sub-matrix (unraveled)
    2. offset: 3x1 offset'''

def transformation_from_reg_dcm(reg_dicom):
    RegistrationSequence = reg_dicom.RegistrationSequence
    Item_2 = RegistrationSequence[1]
    MatrixRegistrationSequence = Item_2.MatrixRegistrationSequence
    Item_1_1 = MatrixRegistrationSequence[0]
    MatrixSequence = Item_1_1.MatrixSequence
    Item_1_2 = MatrixSequence[0]
    T = Item_1_2.FrameOfReferenceTransformationMatrix
    T = np.asarray(T)
    TM = np.reshape(T, (4, 4))
    TM = linalg.inv(TM)

    # Get 3x3 rotation sub-matrix
    Mr = TM[0:3, 0:3]
    r = Mr.ravel()

    # Get offset
    offset = TM[0:3, 3]

    return r, offset


def get_date_name(ct_image):
    # Get date and series description from metadata - to be used in filename of nifti file
    study_date = ct_image.GetMetaData('0008,0020')  # Date
    month = str(study_date[4:6])
    day = str(study_date[-2:])
    series_description = ct_image.GetMetaData('0008,103e')

    month_dict = {
        "01": "Jan",
        "02": "Feb",
        "03": "Mar",
        "04": "Apr",
        "05": "May",
        "06": "Jun",
        "07": "Jul",
        "08": "Aug",
        "09": "Sep",
        "10": "Oct",
        "11": "Nov",
        "12": "Dec"
    }

    month_name = month_dict[month]
    date_name = month_name + day + '.nii.gz'
    if 'CBCT' in series_description:
        fname = 'CBCT' + '_' + date_name
    else:
        fname = 'CT' + '_' + date_name

    return fname

