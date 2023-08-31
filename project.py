import numpy as np
import matplotlib.pyplot as plt
import math
import pandas as pd
import random as r 

# Creating a cache for storing the parabolas and MSE values
parabola_cache = {}
mse_cache = {}

# Load the data
def import_csv(filename):
    """
    Import data from a CSV file, convert it to a NumPy array, and perform angle-based sorting and index shifting.
    
    Input:
        filename (str): The path to the CSV file containing points in a specific format.
        
    Output:
        points (numpy.ndarray): An array containing the sorted and shifted points.
        
    The function does the following:
    1. Reads the CSV and extracts points as tuples.
    2. Converts the list of tuples to a NumPy array.
    3. Computes the mean point in the XY plane.
    4. Sorts the points based on their angles with respect to the mean point.
    5. Shifts the indices of the points based on their proximity to the mean x-coordinate.
    """
        
    points = []
    data = pd.read_csv(filename)
    for i, row in data.iterrows():
        point = (row['X'].split()[0], row['X'].split()[1], row['X'].split()[2])
        points.append(point)
        
    points = np.array(points).astype(float)

    # "ANGLE MANNER"
    # Compute the mean of the points in the XY plane
    mean_point = np.mean(points[:, :2], axis=0)

    # Compute the angle for each point with respect to the mean point
    angles = [math.atan2(p[1] - mean_point[1], p[0] - mean_point[0]) for p in points[:, :2]]
    
    # Sort the points based on these angles
    sorted_indices = np.argsort(angles)
    points = points[sorted_indices]

    # SHIFTING
    # Compute the mean of the x-coordinates
    mean_x = np.mean(points[:, 0])

    # Find the point closest to the mean x-coordinate
    start_index = np.argmin(np.abs(points[:, 0] - mean_x))

    # Create an array of indices
    indices = np.arange(len(points))

    # Shift the indices
    shifted_indices = (indices + start_index - 1) % len(points)

    # Reorder the points based on the shifted indices
    points = points[shifted_indices]
    
    return points

# Euclidean distance squered
def euc_dist(a, b):
    """
    Calculate the squared Euclidean distance between two points in a 2D space.
    
    Input:
        a (tuple): The coordinates (x, y) of the first point.
        b (tuple): The coordinates (x, y) of the second point.
        
    Output:
        float: The squared Euclidean distance between points a and b.
    """

    return (a[0]-b[0])**2 + (a[1]-b[1])**2

def generate_parab(start, end, distances):
    """
    Generate a parabolic function based on a given range of indices and distances.
    
    Input:
        start (int): The starting index for the subset of distances.
        end (int): The ending index for the subset of distances.
        distances (numpy.ndarray): An array containing distances.
        
    Output:
        parab (numpy.poly1d): A parabolic function fitted to the subset of distances.
        
    The function also uses a cache to store previously calculated parabolas to avoid redundant calculations.
    """

    # Use start and end as the unique key for caching
    key = (start, end)
    
    # Check if the result is already in the cache
    if key in parabola_cache:
        return parabola_cache[key]
    
    # Calculate x and y based on start and end indices
    x = np.array(range(start, end))
    y = distances[start:end]
    
    # If not in cache, calculate the parabola and store in cache
    parab = np.poly1d(np.polyfit(x, y, 2))
    parabola_cache[key] = parab
    
    return parab

def MSE(start, end, distances, parab):
    """
    Calculate the Mean Squared Error (MSE) between the observed distances and a parabolic fit.
    
    Input:
        start (int): The starting index for the subset of distances.
        end (int): The ending index for the subset of distances.
        distances (numpy.ndarray): An array containing distances.
        parab (numpy.poly1d): A parabolic function to compare against.
        
    Output:
        mse_value (float): The calculated MSE value.
        
    The function uses a cache to store previously calculated MSE values to avoid redundant calculations.
    """
        
    # Use start and end as the unique key for caching
    key = (start, end)
    
    # Check if the result is already in the cache
    if key in mse_cache:
        return mse_cache[key]
    
    # Calculate x and y based on start and end indices
    x = np.array(range(start, end))
    y = distances[start:end]
    
    # If not in cache, calculate the MSE and store in cache
    mse_value = np.sum((y - parab(x))**2)
    mse_cache[key] = mse_value
    
    return mse_value

# Find the path of length k
def segment(n, k, distances):
    """
    Perform dynamic programming to segment a set of distances into 'k' segments, each represented by a parabola.
    
    Input:
        n (int): The total number of points.
        k (int): The number of segments.
        distances (numpy.ndarray): An array containing distances.
        
    Output:
        path (list): A list of indices that represent the best segmentation.
        
    The function utilizes dynamic programming to efficiently find the best segmentation based on MSE.
    """
        
    D = np.full((n+1, k+1), np.inf)
    P = np.full((n+1, k+1), -1)

    D[0, 0] = 0

    # The dynammic programming is done efficiently using the calculations of previous length
    for length in range(1, k + 1):
        # Iterate over each possible ending point of the segment
        for end in range(length, n + 1):
            min_dist = np.inf
            min_index = -1
            
            # Iterate over each possible starting point of the segment
            for start in range(end - length + 1):
                if end - start < 3: # Skip if not enough points to fit a parabola
                    continue

                # Generate parabola (if didn't already) for the segment and calculate its MSE (weight)
                parab = generate_parab(start, end, distances)
                mse = MSE(start, end, distances, parab)
                
                # always keep the best
                if D[start, length - 1] + mse < min_dist:
                    min_dist = D[start, length - 1] + mse
                    min_index = start

            # Update phase in the DP    
            D[end, length] = min_dist
            P[end, length] = min_index

    # Reconstruction phase
    path = []
    current = P[n,k]
    for i in range(k, 0, -1):
        path.append(current - 1)
        current = P[current, i]
    path.reverse()
    return path

def ransac_z_fit(points, iterations=100, threshold=0.5):
    """
    Perform RANSAC to find the most frequent z-coordinate within a given threshold.
    
    Input:
        points (numpy.ndarray): An array containing 3D points.
        iterations (int): The number of iterations for RANSAC. Default is 100.
        threshold (float): The distance threshold for inliers. Default is 0.5.
        
    Output:
        best_z (float): The z-coordinate with the most inliers.
        best_inliers (int): The number of inliers for the best z-coordinate.
    """
        
    best_z = None
    best_inliers = 0
    for _ in range(iterations):
        # Randomly sample a point
        sample = points[np.random.choice(points.shape[0], 1, replace=False)]
        sample_z = sample[0, 2]
        
        # Count inliers within the threshold
        inliers = np.sum(np.abs(points[:, 2] - sample_z) < threshold)
        
        if inliers > best_inliers:
            best_inliers = inliers
            best_z = sample_z
    
    return best_z, best_inliers

def plot_parab(range_start, range_end, distances):
    """
    Generate x and y values to plot a parabolic function based on a given range and distances.
    
    Input:
        range_start (int): The starting index for the range of distances.
        range_end (int): The ending index for the range of distances.
        distances (numpy.ndarray): An array containing distances.
        
    Output:
        x (numpy.ndarray): The x values for plotting.
        Y (numpy.ndarray): The y values for plotting, based on the parabolic fit.
    """
        
    x = np.arange(range_start, range_end + 1)
    y = distances[range_start:range_end + 1]
    parab = generate_parab(range_start, range_end, distances)
    Y = parab(x)
    return x, Y

def bounding_box_3d(points):
    """
    Compute and visualize a 3D bounding box for a set of points.
    
    Input:
        points (numpy.ndarray): An array containing 3D points.
        
    Output:
        rectangle_3d (list): A list of tuples representing the 3D bounding box corners.
        
    The function performs the following tasks:
    1. Estimates a 2D bounding box in the XY plane using a dynamic programming approach.
    2. Visualizes the 2D bounding box and the segmented parabolas.
    3. Estimates the floor and ceiling heights using RANSAC.
    4. Constructs and returns the 3D bounding box.
    """
        
    # Use original 2D rectangle estimation method on XY plane
    n = len(points)
    k = 4

    # Calculate the mean of the XY coordinates
    c_mean = points[:, :2].mean(axis=0)
    # Compute distances from each point to the mean point
    distances = [euc_dist(points[i, :2], c_mean) for i in range(n)]
    # Segment the distances into k segments using the dynamic programming approach
    path = segment(n, k, distances)
    path_points = points[path]

    # Define the corners of the 2D rectangle in XY plane
    sorted_indices = np.argsort(path_points[:, 0])
    path_x = path_points[sorted_indices]
    sorted_indices = np.argsort(path_points[:, 1])
    path_y = path_points[sorted_indices]
    avg = lambda x, y: (x+y)/2
    lower_left = (avg(path_x[0][0], path_x[1][0]), avg(path_y[0][1], path_y[1][1]))
    lower_right = (avg(path_x[2][0], path_x[3][0]), avg(path_y[0][1], path_y[1][1]))
    upper_right = (avg(path_x[2][0], path_x[3][0]), avg(path_y[2][1], path_y[3][1]))
    upper_left = (avg(path_x[0][0], path_x[1][0]), avg(path_y[2][1], path_y[3][1]))

    rectangle = [lower_left, lower_right, upper_right, upper_left]

    # Visualization of 2D bounding box estimation
    plt.scatter(points[:, 0], points[:, 1], s=5)
    # Red edges (estimation from the parabolas themselves)
    plt.plot(points[path, 0], points[path, 1], color='red', linestyle = '--')
    plt.plot([points[path[-1], 0], points[path[0], 0]], [points[path[-1], 1], points[path[0], 1]], color='red', linestyle='--')
    # Green rectangle (returned rectangle - "mean" rectangle derived from the red shape)
    rectangle_points = np.array(rectangle + [lower_left]) 
    plt.plot(rectangle_points[:, 0], rectangle_points[:, 1], color='green')
    plt.show()

    # Plotting the signal function
    plt.scatter(np.linspace(1, n, n), distances)

    # Plotting the parabola for the first segment
    x, y = plot_parab(0, path[0], distances)
    plt.plot(x, y)

    # Plotting the parabolas for the segments defined by the path
    for i in range(len(path) - 1):
        x, y = plot_parab(path[i], path[i + 1], distances)
        plt.plot(x, y)

    # Plotting the last parabola
    x, y = plot_parab(path[-1], len(distances) - 1, distances)
    plt.plot(x, y)
    plt.show()

    # RANSAC-based estimation of floor and ceiling heights
    floor_z, _ = ransac_z_fit(points[points[:, 2] < np.median(points[:, 2])])
    ceiling_z, _ = ransac_z_fit(points[points[:, 2] > np.median(points[:, 2])])

    # Construct 3D bounding box
    rectangle_3d = [
        (lower_left[0], lower_left[1], floor_z),
        (lower_right[0], lower_right[1], floor_z),
        (upper_right[0], upper_right[1], floor_z),
        (upper_left[0], upper_left[1], floor_z),
        (lower_left[0], lower_left[1], ceiling_z),
        (lower_right[0], lower_right[1], ceiling_z),
        (upper_right[0], upper_right[1], ceiling_z),
        (upper_left[0], upper_left[1], ceiling_z)
    ]

    return rectangle_3d

points_3d = import_csv("map.csv")
estimated_bounding_box = bounding_box_3d(points_3d)


# Visualisation
fig = plt.figure()
ax = fig.add_subplot(111, projection='3d')
ax.scatter(points_3d[:, 0], points_3d[:, 1], points_3d[:, 2], c='blue', marker='o', s=40, label="Points")
for i in range(4):
    ax.plot([estimated_bounding_box[i][0], estimated_bounding_box[i+4][0]], 
            [estimated_bounding_box[i][1], estimated_bounding_box[i+4][1]], 
            [estimated_bounding_box[i][2], estimated_bounding_box[i+4][2]], c='green')
for i in range(4):
    ax.plot([estimated_bounding_box[i][0], estimated_bounding_box[(i+1)%4][0]], 
            [estimated_bounding_box[i][1], estimated_bounding_box[(i+1)%4][1]], 
            [estimated_bounding_box[i][2], estimated_bounding_box[(i+1)%4][2]], c='green')
for i in range(4):
    ax.plot([estimated_bounding_box[i+4][0], estimated_bounding_box[(i+1)%4+4][0]], 
            [estimated_bounding_box[i+4][1], estimated_bounding_box[(i+1)%4+4][1]], 
            [estimated_bounding_box[i+4][2], estimated_bounding_box[(i+1)%4+4][2]], c='green')
ax.set_xlabel('X')
ax.set_ylabel('Y')
ax.set_zlabel('Z')
ax.set_title("Estimated 3D room")
ax.legend()
plt.show()
