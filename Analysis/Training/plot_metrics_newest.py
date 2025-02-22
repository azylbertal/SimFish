import matplotlib.pyplot as plt
import numpy as np

from Analysis.Training.load_from_logfiles import load_all_log_data, order_metric_data


def interpolate_metric_data(data, scaffold_points):
    scaffold_points = np.array(scaffold_points)
    scaffold_points = scaffold_points[scaffold_points[:, 1].argsort()]
    previous_switch_ep = 0

    for s in scaffold_points:
        switch_ep = s[0]
        data_before_switch = (data[:, 0] < switch_ep) * (data[:, 0] >= previous_switch_ep)

        switch_ep_difference = switch_ep - previous_switch_ep
        data[data_before_switch, 0] -= previous_switch_ep
        data[data_before_switch, 0] /= switch_ep_difference
        data[data_before_switch, 0] += (s[1] - 1)

        previous_switch_ep = switch_ep

    data_before_switch = (data[:, 0] >= previous_switch_ep)
    switch_ep_difference = np.sum(data_before_switch * 1) * 2

    data[data_before_switch, 0] -= previous_switch_ep
    data[data_before_switch, 0] /= switch_ep_difference
    data[data_before_switch, 0] += s[1]

    return data


def compute_rolling_averages_over_data(data, window):
    data_points = data.shape[0]
    data_points_cut = data_points - window
    rolling_average = np.array([[np.mean(data[i: i + window, 1])] for i in range(data_points) if i < data_points_cut])
    steps_cut = data[:data_points_cut, 0:1]

    rolling_average = np.concatenate((steps_cut, rolling_average), axis=1)
    return rolling_average


def get_metric_name(metric_label):
    if metric_label == "prey caught":
        metric_name = "Prey Caught (per episode)"

    elif metric_label == "capture success rate":
        metric_name = "Capture Success Rate"

    elif metric_label == "prey capture rate (fraction caught per step)":
        metric_name = "Prey Capture Rate (fraction caught per step)"

    elif metric_label == "Energy Efficiency Index":
        metric_name = "Energy Efficiency Index"

    elif metric_label == "Episode Duration":
        metric_name = "Episode Duration"

    elif metric_label == "Mean salt damage taken per step":
        metric_name = "Salt Damage (mean per step)"

    elif metric_label == "Phototaxis Index":
        metric_name = "Phototaxis Index"

    elif metric_label == "episode reward":
        metric_name = "Episode Reward"

    elif metric_label == "predator avoidance index (avoided":
        metric_name = "Predator Avoidance Index"

    elif metric_label == "predators avoided":
        metric_name = "Predators Avoided"

    else:
        metric_name = metric_label

    return metric_name


def plot_multiple_metrics_multiple_models(model_list, metrics, window, interpolate_scaffold_points, figure_name):
    """Different to previous versions in that it uses data directly from log files, and scales points between scaffold
    switching points to allow plotting between models. The resulting graph is x: config change point, y: metric.

    window is the window for computing the rolling averages for each metric.
    """

    model_data = [load_all_log_data(model) for model in model_list]
    ordered_chosen_model_data = [{metric: order_metric_data(model[metric]) for metric in metrics} for model in
                                 model_data]

    ordered_chosen_model_data_rolling_averages = [
        {metric: compute_rolling_averages_over_data(model[metric], window) for metric
         in metrics} for model in ordered_chosen_model_data]
    # episodes = np.array(ordered_chosen_model_data_rolling_averages[0]["prey caught"])[:, 0]
    # plt.plot(sorted(episodes))
    # plt.show()

    if interpolate_scaffold_points:
        # TODO: Problem below here
        scaffold_switching_points = [model["Configuration change"] for model in model_data]
        new_orders = [np.argsort(np.array(model)[:, 1]) for model in scaffold_switching_points]
        scaffold_switching_points = [np.array(model)[new_orders[i]] for i, model in
                                     enumerate(scaffold_switching_points)]
        ordered_chosen_model_data_rolling_averages = [{metric: interpolate_metric_data(model[metric],
                                                                                       scaffold_switching_points[i])
                                                       for metric in metrics} for i, model in
                                                      enumerate(ordered_chosen_model_data_rolling_averages)]

    num_metrics = len(metrics)
    fig, axs = plt.subplots(num_metrics, 1, figsize=(15, int(4 * num_metrics)), sharex=True)
    for model in ordered_chosen_model_data_rolling_averages:
        for i, metric in enumerate(metrics):
            metric_name = get_metric_name(metric)

            if metric_name == "Phototaxis Index":
                to_switch = (model[metric][:, 0] < 31)
                model[metric][to_switch, 1] -= 0.5
                model[metric][to_switch, 1] *= 2
            axs[i].plot(model[metric][:, 0], model[metric][:, 1])

            axs[i].set_ylabel(metric_name)
            axs[i].grid(True, axis="x")

    axs[-1].set_xlabel("Scaffold Point")
    sc = np.concatenate(([np.array(s) for s in scaffold_switching_points]))
    axs[-1].set_xticks([int(t) for t in np.linspace(0, np.max(sc[:, 1]))])
    axs[-1].set_xlim(1, np.max(sc[:, 1]) + 1)

    plt.savefig(f"Plots/{figure_name}.jpg")
    plt.clf()
    plt.close()


def plot_scaffold_durations(model_name):
    data = load_all_log_data(model_name)
    scaffold_switching_points = np.array(data["Configuration change"])
    scaffold_switching_points = scaffold_switching_points[scaffold_switching_points[:, 1].argsort()]

    config = scaffold_switching_points[:, 1]
    episode = scaffold_switching_points[:, 0]
    duration = [d - episode[i - 1] if i > 0 else d for i, d in enumerate(episode)]
    plt.plot(config, duration)
    plt.show()


if __name__ == "__main__":
    # models = ["ppo_scaffold_22-1", "ppo_scaffold_22-2"]
    dqn_models_old = ["dqn_scaffold_26-1", "dqn_scaffold_26-2"]  # , "dqn_scaffold_26-3", "dqn_scaffold_26-4"]
    # models = ["dqn_scaffold_27-1", "dqn_scaffold_27-2"]
    dqn_models = ["dqn_scaffold_30-1", "dqn_scaffold_30-2"]
    ppo_models = ["ppo_scaffold_21-1", "ppo_scaffold_21-2"]

    """Possible metrics:
       - "prey capture index (fraction caught)"
       - "prey capture rate (fraction caught per step)"
       - "Energy Efficiency Index
       - "Episode Duration"
       - "Mean salt damage taken per step"
       - "Phototaxis Index"
       - "capture success rate"
       - "episode reward"
       - "predator avoidance index (avoided/p_pred)"
       - "predators avoided"
       - "prey caught"
       - "Exploration Quotient"
       - "turn chain preference"                      
       - "Cause of Death"
    """
    chosen_metrics_dqn = ["prey capture index (fraction caught)",
                          "capture success rate",
                          # "episode reward",
                          # "Energy Efficiency Index",
                          "Episode Duration",
                          # "Exploration Quotient",
                          # "turn chain preference",
                          # "Cause of Death",
                          # Sand grain attempted captures.
                          # DQN only
                          # "predator avoidance index (avoided/p_pred)",
                          "Phototaxis Index"
                          ]
    chosen_metrics_ppo = ["prey capture index (fraction caught)",
                          "capture success rate",
                          # "episode reward",
                          # "Energy Efficiency Index",
                          "Episode Duration",
                          # "Exploration Quotient",
                          # "turn chain preference",
                          # "Cause of Death",
                          # Sand grain attempted captures.
                          # DQN only
                          # "predator avoidance index (avoided/p_pred)",
                          # "Phototaxis Index"
                          ]
    plot_multiple_metrics_multiple_models(dqn_models, chosen_metrics_dqn, window=40, interpolate_scaffold_points=True,
                                          figure_name="dqn_30")
    plot_multiple_metrics_multiple_models(ppo_models, chosen_metrics_ppo, window=40, interpolate_scaffold_points=True,
                                          figure_name="ppo_21")
    # plot_scaffold_durations(models[0])
