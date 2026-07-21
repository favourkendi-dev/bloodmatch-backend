from math import radians, sin, cos, sqrt, atan2


def calculate_distance_km(lat1, lon1, lat2, lon2):
    """
    Returns the distance in kilometers between two lat/long points,
    using the Haversine formula (great-circle distance on a sphere).
    """
    earth_radius_km = 6371

    lat1, lon1, lat2, lon2 = map(radians, [float(lat1), float(lon1), float(lat2), float(lon2)])

    delta_lat = lat2 - lat1
    delta_lon = lon2 - lon1

    a = sin(delta_lat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(delta_lon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    return earth_radius_km * c
