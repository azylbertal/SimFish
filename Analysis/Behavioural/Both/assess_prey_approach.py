import numpy as np
import matplotlib.pyplot as plt


from Analysis.load_data import load_data


def get_prey_capture_timestamps(data):
    consumptions = [i for i, c in enumerate(data["consumed"]) if c == 1]
    prey_capture_sequences_t = [[i for i in range(c-9, c+1)] for c in consumptions]
    return prey_capture_sequences_t


def get_fish_prey_relationships(data, sequences):
    fish_prey_angles_compiled = []
    fish_prey_distances_compiled = []
    for s in sequences:
        fish_angles = data["fish_angle"][s]
        fish_positions = data["fish_position"][s]
        prey_positions = data["prey_positions"][s]

        # Finding the relevant prey.
        final_fs = fish_positions[-2]
        final_ps = prey_positions[-2, :, :]
        distances = final_fs - final_ps
        distances = (distances[:, 0] ** 2 + distances[:, 1] ** 2) ** 0.5
        chosen_prey = np.argmin(distances)

        prey_positions = prey_positions[:, chosen_prey]

        fish_prey_vectors = prey_positions - fish_positions
        fish_prey_distances = (fish_prey_vectors[:, 0] ** 2 + fish_prey_vectors[:, 1] ** 2) ** 0.5

        # Will generate values between -pi/2 and pi/2 which require adjustment depending on quadrant.
        fish_prey_angles = np.arctan(fish_prey_vectors[:, 1] / fish_prey_vectors[:, 0]) - fish_angles
        fish_prey_angles %= np.pi
        # Adjust so between -pi/2 and pi/2
        higher_portion = (fish_prey_angles > np.pi/2)
        fish_prey_angles[higher_portion] -= np.pi

        fish_prey_angles_compiled.append(fish_prey_angles[:-1])
        fish_prey_distances_compiled.append(fish_prey_distances[:-1])

    fish_prey_angles_compiled = np.array(fish_prey_angles_compiled)
    fish_prey_distances_compiled = np.array(fish_prey_distances_compiled)
    return fish_prey_distances_compiled, fish_prey_angles_compiled


if __name__ == "__main__":
    dist = []
    angs = []
    model_name, assay_config, assay_id, n = "ppo_scaffold_21-1", "Behavioural-Data-Free", f"Naturalistic", 10
    for i in range(1, n+1):
        d = load_data(model_name, assay_config, f"{assay_id}-{i}")
        ts = get_prey_capture_timestamps(d)
        dis, ang = get_fish_prey_relationships(d, ts)
        if dis.shape[0] > 0:
            dist.append(dis)
        if ang.shape[0] > 0:
            angs.append(ang)

    dist = np.concatenate((dist))
    angs = np.concatenate((angs))

    mean_dist = np.mean(dist, axis=0)
    mean_ang = np.mean(np.absolute(angs), axis=0)

    plt.plot(np.swapaxes(angs, 0, 1), color="grey", alpha=0.5)
    plt.plot(mean_ang, color="r")
    plt.xlabel("Bouts before consumption")
    plt.ylabel("Angle to prey (pi radians)")
    plt.savefig(f"{model_name}-fish_prey_angle.jpg")
    plt.clf()
    plt.close()

    plt.plot(np.swapaxes(dist, 0, 1)/10, color="grey", alpha=0.5)
    plt.plot(mean_dist/10, color="r")
    plt.xlabel("Bouts before consumption")
    plt.ylabel("Distance from Prey (mm)")
    plt.ylim(0, 10)
    plt.savefig(f"{model_name}-fish_prey_distance.jpg")
    plt.clf()
    plt.close()
