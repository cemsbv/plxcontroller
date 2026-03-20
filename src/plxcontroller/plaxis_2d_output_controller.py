from __future__ import annotations

import os
import subprocess
import time

import numpy as np
import pandas as pd
from plxscripting.plxproxy import PlxProxyGlobalObject
from plxscripting.server import Server, new_server

from plxcontroller.plaxis_2d_input_controller import Plaxis2DInputController


class Plaxis2DOutputController:
    def __init__(self) -> None:
        """Creates a new Plaxis2DOutputController instance."""
        self._server: Server | None = None
        self._subprocess: subprocess.Popen | None = None
        self._filepath: str | None = None

    @property
    def s_o(self) -> Server | None:
        """Returns the server object. This is a typical alias for the server object."""
        return self._server

    @property
    def g_o(self) -> PlxProxyGlobalObject | None:
        """Returns the global project object. This is a typical alias for the global project object."""
        if isinstance(self._server, Server):
            return self._server.plx_global
        return None

    def connect(self, ip_address: str = "localhost", port: int = 10001) -> None:
        """Starts a new Plaxis instance and a new server connection with the given IP address and port and
        connect to it.

        Args:
            ip_address (str): the IP address of the Plaxis server. Defaults to "localhost".
            port (int, optional): the port to of the Plaxis server. Defaults to 10001.
        """

        plaxis_path = os.getenv("PLAXIS_2D_OUTPUT_PROGRAM")
        if not plaxis_path:
            raise ValueError(
                'Environmental variable "PLAXIS_2D_OUTPUT_PROGRAM" is not set.'
            )
        if not os.path.exists(plaxis_path):
            raise ValueError(
                f'PLAXIS 2D Output program path "{plaxis_path}" does not exist.'
            )

        password = os.getenv("PLAXIS_2D_PASSWORD")
        if not password:
            raise ValueError('Environmental variable "PLAXIS_2D_PASSWORD" is not set.')

        # Create subprocess
        self._subprocess = subprocess.Popen(
            [
                plaxis_path,
                f"--AppServerPort={port}",
                f"--AppServerPassword={password}",
            ],
        )

        # Connect to PLAXIS remote server
        server, _ = new_server(ip_address, port, password=password)

        # Store the server
        self._server = server

    def open(self, filepath: str) -> None:
        """Open a PLAXIS model file.

        Args:
            filepath (str): the path to the PLAXIS model file.
        """
        if not self._server:
            raise ValueError("No server connection available.")

        self._server.open(filepath)
        self._filepath = filepath

    def close(self) -> None:
        """Close the PLAXIS model file."""
        if not self._server:
            raise ValueError("No server connection available.")

        self._server.close()
        self._filepath = None

    def disconnect(self) -> None:
        """Disconnect from the PLAXIS server."""

        if self._subprocess is not None and self._subprocess.stdin is not None:
            plaxis_path = os.getenv("PLAXIS_2D_OUTPUT_PROGRAM")
            if isinstance(plaxis_path, str):
                self._subprocess.stdin.write(f"taskkill /IM {plaxis_path}\n".encode())
            self._subprocess.terminate()

        self._server = None
        self._subprocess = None
        self._filepath = None

    def retrieve_node_locations(self):

        # node locations
        node_locations = pd.DataFrame(columns=['name', 'x', 'y', 'z'])
        for i, node in enumerate(self.g_o.Nodes):
            node_locations.at[i] = [node.Name.value, node.x.value, node.y.value, node.z.value]

        return node_locations

    def retrieve_precalc_node_outputs(self, phase_number: int, result_types: list, time_type='dynamic'):

        # Open input program to retrieve phase input data (this is much faster than retrieving it from the output program)
        server, _ = new_server(
            self.server.connection.host, port, password=self.server.connection._password
        )
        co = Plaxis2DInputController(server)


        phase = getattr(self.g_o, f"Phase_{phase_number}")
        
        # Get step output V1.
        # it is necessary to get the phase input to get faster the first step and the last step
        phase_input = getattr(self.g_i, f"Phase_{phase_number}")
        # phase_start_step = int(phase.Steps[0].Name.__str__().split('Step_')[-1]) # this takes way too long!!
        # phase_end_step = int(phase.Steps[-1].Name.__str__().split('Step_')[-1]) # this takes way too long!!
        phase_start_step = phase_input.FirstStep.value
        phase_end_step = phase_input.LastStep.value
        step_output = np.arange(phase_start_step, phase_end_step + 1, 1, dtype=np.int32)
        
        # # Get time ouput v1
        # previous_phase_name = getattr(self.g_i, f"Phase_{phase_number}").PreviousPhase.Name.value
        # # previous_phase = getattr(self.g_o, previous_phase_name)
        # previous_phase_input = getattr(self.g_i, previous_phase_name)
        # if time_type == 'dynamic':
        #     # phase_start_time = float(previous_phase.Reached.DynamicTime.__str__()) # this takes way too long!!
        #     # phase_end_time = float(phase.Reached.DynamicTime.__str__()) # this takes way too long!!
        #     phase_start_time = previous_phase_input.Reached.DynamicTime.value
        #     phase_end_time = phase_input.Reached.DynamicTime.value
        # else:
        #     # phase_start_time = float(previous_phase.Reached.Time.__str__()) # this takes way too long!!
        #     # phase_end_time = float(phase.Reached.Time.__str__()) # this takes way too long!!
        #     phase_start_time = previous_phase_input.Reached.Time.value
        #     phase_end_time = phase_input.Reached.Time.value
        # time_output = np.linspace(phase_start_time, phase_end_time, len(step_output))

        # Get step number to step object mapping
        step_number_to_step = {}
        for step_number in step_output:
            step_number_to_step[step_number] = getattr(self.g_o, f"Step_{step_number}")

        # Get time output v2
        # step_output = []
        time_output = []
        for step_number in step_output:
            # step_output.append(step.Number.value)
            # time_output.append(phase.Reached.Time.value)
            # time_output.append(getattr(self.g_o, f"Step_{step_number}").Reached.Time.value)
            time_output.append(step_number_to_step[step_number].Reached.Time.value)
        
        # node outputs
        node_outputs = {}
        for _, node in enumerate([a for a in self.g_o.Nodes]): # separate the Nodes and Stress points
            single_node_outputs = pd.DataFrame(
                {
                    'step': step_output,
                    'time': time_output,
                }
            )
            for result_type in result_types:
                plaxis_result_type = getattr(getattr(self.g_o.ResultTypes, result_type.split('.')[0]), result_type.split('.')[1])
                single_node_outputs[result_type] = np.array(
                    self.g_o.getcurveresultspath(node, phase,
                                                    # phase.Steps[-1],  # this takes way too long!!
                                                    # getattr(self.g_o, f"Step_{phase_end_step}"),
                                                    step_number_to_step[phase_end_step],
                                                    plaxis_result_type)
                )
            node_outputs[node.Name.value] = single_node_outputs.copy()

        # store outputs
        return node_outputs