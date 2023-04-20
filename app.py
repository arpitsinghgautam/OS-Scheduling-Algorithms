import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
import base64

class PriorityScheduler:

    def __init__(self, arrival_time, burst_time, priority):
        self.total_processes = len(arrival_time)
        self.proc = []
        for i in range(self.total_processes):
            l = []
            for j in range(4):
                l.append(0)
            self.proc.append(l)
        
        for i in range(self.total_processes):
            self.proc[i][0] = arrival_time[i]
            self.proc[i][1] = burst_time[i]
            self.proc[i][2] = priority[i]
            self.proc[i][3] = i + 1
        
        self.proc = sorted(self.proc, key=lambda x: (x[0], x[2]))
        self.proc = sorted(self.proc)
        
        self.waiting_time = [0] * self.total_processes
        self.turnaround_time = [0] * self.total_processes
        self.start_time = [0] * self.total_processes
        self.complete_time = [0] * self.total_processes
        

    def get_waiting_time(self):
        service = [0] * self.total_processes
        service[0] = 0
        self.waiting_time[0] = 0

        for i in range(1, self.total_processes):
            service[i] = self.proc[i - 1][1] + service[i - 1]
            self.waiting_time[i] = service[i] - self.proc[i][0] + 1
            if self.waiting_time[i] < 0:
                self.waiting_time[i] = 0

    def get_turnaround_time(self):
        for i in range(self.total_processes):
            self.turnaround_time[i] = self.proc[i][1] + self.waiting_time[i]

    def find_gantt_chart(self):
        self.start_time[0] = 1
        self.complete_time[0] = self.start_time[0] + self.turnaround_time[0]
        for i in range(1, self.total_processes):
            self.start_time[i] = self.complete_time[i - 1]
            self.complete_time[i] = self.start_time[i] + self.turnaround_time[i] - self.waiting_time[i]

    def schedule(self):
        self.get_waiting_time()
        self.get_turnaround_time()
        self.find_gantt_chart()

        process_data = []
        for i in range(self.total_processes):
            process_data.append([self.proc[i][3], self.start_time[i], self.complete_time[i], self.turnaround_time[i], self.waiting_time[i]])

        df = pd.DataFrame(process_data, columns=["Process_no", "Start_time", "Complete_time", "Turn_Around_Time", "Waiting_Time"])
        avg_tat = sum(self.turnaround_time) / self.total_processes
        avg_waiting_time = sum(self.waiting_time) / self.total_processes

        print("Process Details:")
        print(df)
        print("Average Turnaround Time: ", avg_tat)
        print("Average Waiting Time: ", avg_waiting_time)

        return df, avg_tat, avg_waiting_time


class RoundRobinScheduler:
    def __init__(self, tq, n, arrival, burst):
        self.tq = tq
        self.n = n
        self.arrival = arrival
        self.burst = burst
        self.wait = [0] * n
        self.turn = [0] * n
        self.queue = [0] * n
        self.temp_burst = burst.copy()
        self.complete = [False] * n
        self.timer = 0
        self.maxProccessIndex = 0
        self.avgWait = 0
        self.avgTT = 0
        self.df = None

    def queueUpdation(self, maxProccessIndex):
        zeroIndex = -1
        for i in range(self.n):
            if self.queue[i] == 0:
                zeroIndex = i
                break

        if zeroIndex == -1:
            return
        self.queue[zeroIndex] = maxProccessIndex + 1

    def checkNewArrival(self):
        if self.timer <= self.arrival[self.n - 1]:
            newArrival = False
            for j in range(self.maxProccessIndex + 1, self.n):
                if self.arrival[j] <= self.timer:
                    if self.maxProccessIndex < j:
                        self.maxProccessIndex = j
                        newArrival = True

            # adds the index of the arriving process(if any)
            if newArrival:
                self.queueUpdation(self.maxProccessIndex)

    def queueMaintenance(self):
        for i in range(self.n - 1):
            if self.queue[i + 1] != 0:
                self.queue[i], self.queue[i + 1] = self.queue[i + 1], self.queue[i]

    def run(self):
        while self.timer < self.arrival[0]:
            # Incrementing Timer until the first process arrives
            self.timer += 1
        self.queue[0] = 1

        while True:
            flag = True
            for i in range(self.n):
                if self.temp_burst[i] != 0:
                    flag = False
                    break

            if flag:
                break

            for i in range(self.n and self.queue[i] != 0):
                ctr = 0
                while ctr < self.tq and self.temp_burst[self.queue[0] - 1] > 0:
                    self.temp_burst[self.queue[0] - 1] -= 1
                    self.timer += 1
                    ctr += 1

                    # Updating the ready queue until all the processes arrive
                    self.checkNewArrival()

                if self.temp_burst[self.queue[0] - 1] == 0 and self.complete[self.queue[0] - 1] == False:
                    # turn currently stores exit times
                    self.turn[self.queue[0] - 1] = self.timer
                    self.complete[self.queue[0] - 1] = True

                # checks whether or not CPU is idle
                idle = True
                if self.queue[self.n - 1] == 0:
                    for k in range(self.n):
                        if self.queue[k] != 0:
                            if self.complete[self.queue[k] - 1] == False:
                                idle = False
                else:
                    idle = False

                if idle:
                    self.timer += 1
                    self.checkNewArrival()

                # Maintaining the entries of processes after each preemption in the ready Queue
                self.queueMaintenance()

    def calculateAverageWaitTime(self):
        totalWait = 0
        for i in range(self.n):
            self.wait[i] = self.turn[i] - self.arrival[i] - self.burst[i]
            totalWait += self.wait[i]
        self.avgWait = totalWait / self.n

    def calculateAverageTurnaroundTime(self):
        totalTT = 0
        for i in range(self.n):
            self.turn[i] = self.turn[i] - self.arrival[i]
            totalTT += self.turn[i]
        self.avgTT = totalTT / self.n

    def generateGanttChart(self):
        ganttChart = []
        for i in range(self.n):
            process = "P" + str(self.queue[i])
            ganttChart.append(process)
        return ganttChart

    def displayResult(self):
        self.calculateAverageWaitTime()
        self.calculateAverageTurnaroundTime()
        ganttChart = self.generateGanttChart()

        self.df = pd.DataFrame({'Process': ganttChart,
                                'Arrival_Time': self.arrival,
                                'Burst_Time': self.burst,
                                'Waiting_Time': self.wait,
                                'Turn_Around_Time': self.turn})
	
        print("Gantt Chart:")
        print(" -> ".join(ganttChart))
        print("\nAverage Waiting Time:", self.avgWait)
        print("Average Turnaround Time:", self.avgTT)

        print("\nProcess Details:")
        print(self.df)

    def schedule(self):
        self.run()
        self.displayResult()
        return self.df, self.avgWait, self.avgTT



class FCFS:
    def __init__(self, processes, burst_time, arrival_time):
        self.processes = processes
        self.burst_time = burst_time
        self.arrival_time = arrival_time
        self.n = len(processes)
        
    def findWaitingTime(self):
        service_time = [0] * self.n
        service_time[0] = 0
        wt = [0] * self.n

        for i in range(1, self.n):
            service_time[i] = (service_time[i - 1] + self.burst_time[i - 1])
            wt[i] = service_time[i] - self.arrival_time[i]
            if (wt[i] < 0):
                wt[i] = 0
        return wt
    
    def findTurnAroundTime(self, wt):
        tat = [0] * self.n
        for i in range(self.n):
            tat[i] = self.burst_time[i] + wt[i]
        return tat
    
    def findavgTime(self):
        wt = self.findWaitingTime()
        tat = self.findTurnAroundTime(wt)
        total_wt = sum(wt)
        total_tat = sum(tat)
        compl_time = [tat[i] + self.arrival_time[i] for i in range(self.n)]
        
        # Creating a dictionary to store the results
        result = {
            'Process': self.processes,
            'Burst_Time': self.burst_time,
            'Arrival_Time': self.arrival_time,
            'Waiting_Time': wt,
            'Turn_Around_Time': tat,
            'Completion_Time': compl_time
        }
        
        # Creating a Pandas DataFrame from the dictionary
        df = pd.DataFrame(result)
        avg_wt = total_wt / self.n
        avg_tat = total_tat / self.n
        print("Average waiting time = %.5f" % avg_wt)
        print("Average turn around time = %.5f" % avg_tat)
        return df, avg_wt, avg_tat




# Streamlit UI
def main():
    image_file = 'background.jpg'

    with open(image_file, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read())
    st.markdown(
        f"""
        <style>
        .stApp {{
            background-image: url(data:image/{"png"};base64,{encoded_string.decode()});
            background-size: cover
        }}
        </style>
        """,
        unsafe_allow_html=True
        )
    st.title("Task Scheduling Algorithms")
    st.write("Enter task details below:")
    task_count = st.number_input("Number of tasks", min_value=1, step=1, value=3)
    processes = []
    for i in range(1,task_count+1):
        processes.append(i)
    print("The number of process are:  ", processes)
    arrival_time_list = []
    burst_time_list = []
    priority_list = []
    for i in range(task_count):
        task_id = i + 1
        arrival_time = st.number_input(f"Arrival time for Task {task_id}", step=1, value=0)
        burst_time = st.number_input(f"Burst time for Task {task_id}", step=1, value=1)
        priority = st.number_input(f"Priority for Task {task_id}", step=1, value=1)
        arrival_time_list.append(arrival_time)
        burst_time_list.append(burst_time)
        priority_list.append(priority)

    time_quantum = st.number_input("Time quantum for Round Robin", step=1, value=1)
    st.write("Select scheduling algorithm:")
    algorithm = st.selectbox("Algorithm", ["First-Come, First-Served", "Round Robin", "Priority"])

    # Perform scheduling based on selected algorithm
    if algorithm == "First-Come, First-Served":
        fcfs = FCFS(processes, burst_time_list, arrival_time_list)
        df, avg_wt, avg_tat = fcfs.findavgTime()
    # elif algorithm == "Shortest Job Next":
    #     waiting_time, turnaround_time = sjn_scheduling(tasks)
    elif algorithm == "Round Robin":
        scheduler = RoundRobinScheduler(time_quantum, task_count, arrival_time_list, burst_time_list)
        df, avg_wt, avg_tat =scheduler.schedule()
    elif algorithm == "Priority":
        scheduler = PriorityScheduler(arrival_time_list, burst_time_list, priority_list)
        df, avg_tat, avg_wt = scheduler.schedule()
        print(df)
        print("Average Turnaround Time:", avg_tat)
        print("Average Waiting Time:", avg_wt) 

    # Calculate average turnaround time and average waiting time
    avg_turnaround_time = avg_tat
    avg_waiting_time = avg_wt

    # Display results
    # df = pd.DataFrame(tasks, columns=["Arrival Time", "Burst Time", "Priority"])
    # df["Waiting Time"] = waiting_time
    # df["Turnaround Time"] = turnaround_time
    st.write("Task scheduling results:")
    st.write(df)
    st.write("Average Turnaround Time:", avg_turnaround_time)
    st.write("Average Waiting Time:", avg_waiting_time)

    # Visualize scheduling process using a bar chart
    fig, ax = plt.subplots(figsize=(10, 5))
    task_names = [f"Task {i+1}" for i in range(task_count)]
    ax.bar(task_names, df["Turn_Around_Time"], label="Turn Around Time")
    ax.bar(task_names, df["Waiting_Time"], label="Waiting Time")
    ax.set_xlabel("Task")
    ax.set_ylabel("Time")
    ax.set_title("Task Scheduling Process")
    ax.legend()
    st.pyplot(fig)

# Run the main function
main()