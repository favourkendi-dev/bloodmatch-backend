# Maps each blood type to the list of donor blood types that are compatible with it
# (i.e. which donor types can give blood to a patient needing this type).
COMPATIBLE_DONORS = {
    'A+':  ['A+', 'A-', 'O+', 'O-'],
    'A-':  ['A-', 'O-'],
    'B+':  ['B+', 'B-', 'O+', 'O-'],
    'B-':  ['B-', 'O-'],
    'AB+': ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-'],  # universal recipient
    'AB-': ['A-', 'B-', 'AB-', 'O-'],
    'O+':  ['O+', 'O-'],
    'O-':  ['O-'],  # only O- can donate to O-
}


def get_compatible_donor_types(requested_blood_type):
    """Returns list of donor blood types compatible with the requested type."""
    return COMPATIBLE_DONORS.get(requested_blood_type, [])
