# Copyright 2018-2021 Xanadu Quantum Technologies Inc.

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#     http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""
Unit tests for the adjoint metric tensor function.
"""
import pytest
from pennylane import numpy as np
import pennylane as qml

from pennylane.transforms.adjoint_metric_tensor import _apply_any_operation


class TestApplyAnyOperation:

    device = qml.device("default.qubit", wires=2)
    x = 0.5

    def test_simple_operation(self):
        op = qml.RX(self.x, wires=0)
        out = _apply_any_operation(self.device._state, op, self.device)
        out = qml.math.reshape(out, 4)
        exp = np.array([np.cos(self.x / 2), 0.0, -1j * np.sin(self.x / 2), 0.0])
        assert np.allclose(out, exp)
        assert not op.inverse

    def test_simple_operation_inv(self):
        op = qml.RX(self.x, wires=0)
        out = _apply_any_operation(self.device._state, op, self.device, invert=True)
        out = qml.math.reshape(out, 4)
        exp = np.array([np.cos(self.x / 2), 0.0, 1j * np.sin(self.x / 2), 0.0])
        assert np.allclose(out, exp)
        assert not op.inverse

    def test_inv_operation(self):
        op = qml.RX(self.x, wires=0).inv()
        out = _apply_any_operation(self.device._state, op, self.device)
        out = qml.math.reshape(out, 4)
        exp = np.array([np.cos(self.x / 2), 0.0, 1j * np.sin(self.x / 2), 0.0])
        assert np.allclose(out, exp)
        assert op.inverse

    def test_inv_operation_inv(self):
        op = qml.RX(self.x, wires=0).inv()
        out = _apply_any_operation(self.device._state, op, self.device, invert=True)
        out = qml.math.reshape(out, 4)
        exp = np.array([np.cos(self.x / 2), 0.0, -1j * np.sin(self.x / 2), 0.0])
        assert np.allclose(out, exp)
        assert op.inverse

    def test_operation_group(self):
        op = [qml.RX(self.x, wires=0).inv(), qml.Hadamard(wires=1), qml.CNOT(wires=[1, 0])]
        out = _apply_any_operation(self.device._state, op, self.device)
        out = qml.math.reshape(out, 4)
        exp = np.array(
            [
                np.cos(self.x / 2) / np.sqrt(2),
                1j * np.sin(self.x / 2) / np.sqrt(2),
                1j * np.sin(self.x / 2) / np.sqrt(2),
                np.cos(self.x / 2) / np.sqrt(2),
            ]
        )
        assert np.allclose(out, exp)
        assert isinstance(op[0], qml.RX) and op[0].inverse
        assert isinstance(op[1], qml.Hadamard) and not op[1].inverse
        assert isinstance(op[2], qml.CNOT) and not op[2].inverse

    def test_operation_group_inv(self):
        op = [qml.RX(self.x, wires=0).inv(), qml.Hadamard(wires=1), qml.CNOT(wires=[1, 0])]
        out = _apply_any_operation(self.device._state, op, self.device, invert=True)
        out = qml.math.reshape(out, 4)
        exp = np.array(
            [
                np.cos(self.x / 2) / np.sqrt(2),
                np.cos(self.x / 2) / np.sqrt(2),
                -1j * np.sin(self.x / 2) / np.sqrt(2),
                -1j * np.sin(self.x / 2) / np.sqrt(2),
            ]
        )
        assert np.allclose(out, exp)
        assert isinstance(op[0], qml.RX) and op[0].inverse
        assert isinstance(op[1], qml.Hadamard) and not op[1].inverse
        assert isinstance(op[2], qml.CNOT) and not op[2].inverse

    def test_qubit_statevector(self):
        state = np.array([0.4, 1.2 - 0.2j, 9.5, -0.3 + 1.1j])
        state /= np.linalg.norm(state, ord=2)
        op = qml.QubitStateVector(state, wires=self.device.wires)
        out = _apply_any_operation(None, op, self.device, invert=False)
        out = qml.math.reshape(out, 4)
        assert np.allclose(out, state)

    def test_error_qubit_statevector(self):
        state = np.array([0.4, 1.2 - 0.2j, 9.5, -0.3 + 1.1j])
        state /= np.linalg.norm(state, ord=2)
        op = qml.QubitStateVector(state, wires=self.device.wires)
        with pytest.raises(ValueError, match="Can't invert state preparation."):
            _apply_any_operation(None, op, self.device, invert=True)

    def test_basisstate(self):
        op = qml.BasisState(np.array([1, 0]), wires=self.device.wires)
        out = _apply_any_operation(None, op, self.device, invert=False)
        out = qml.math.reshape(out, 4)
        exp = np.array([0.0, 0.0, 1.0, 0.0])
        assert np.allclose(out, exp)

    def test_error_basisstate(self):
        op = qml.BasisState(np.array([1, 0]), wires=self.device.wires)
        with pytest.raises(ValueError, match="Can't invert state preparation."):
            _apply_any_operation(None, op, self.device, invert=True)


fixed_pars = np.array([-0.2, 0.2, 0.5, 0.3, 0.7], requires_grad=False)


def fubini_ansatz0(params, wires=None):
    qml.RX(params[0], wires=0)
    qml.RY(fixed_pars[0], wires=0)
    qml.CNOT(wires=[wires[0], wires[1]])
    qml.RZ(params[1], wires=0)
    qml.CNOT(wires=[wires[0], wires[1]])


def fubini_ansatz1(params, wires=None):
    qml.RX(fixed_pars[1], wires=0)
    for wire in wires:
        qml.Rot(*params[0][wire], wires=wire)
    qml.CNOT(wires=[0, 1])
    qml.RY(fixed_pars[1], wires=0)
    qml.CNOT(wires=[1, 2])
    for wire in wires:
        qml.Rot(*params[1][wire], wires=wire)
    qml.CNOT(wires=[1, 2])
    qml.RX(fixed_pars[2], wires=1)


def fubini_ansatz2(params, wires=None):
    params0 = params[0]
    params1 = params[1]
    qml.RX(fixed_pars[1], wires=0)
    qml.Rot(*fixed_pars[2:5], wires=1)
    qml.CNOT(wires=[0, 1])
    qml.RY(params0, wires=0)
    qml.RY(params0, wires=1)
    qml.CNOT(wires=[0, 1])
    qml.RX(params1, wires=0)
    qml.RX(params1, wires=1)


def fubini_ansatz3(params, wires=None):
    params0 = params[0]
    params1 = params[1]
    params2 = params[2]
    qml.RX(fixed_pars[1], wires=0)
    qml.RX(fixed_pars[3], wires=1)
    qml.CNOT(wires=[0, 1])
    qml.CNOT(wires=[1, 2])
    qml.RX(params0, wires=0)
    qml.RX(params0, wires=1)
    qml.CNOT(wires=[0, 1])
    qml.CNOT(wires=[1, 2])
    qml.CNOT(wires=[2, 0])
    qml.RY(params1, wires=0)
    qml.RY(params1, wires=1)
    qml.RY(params1, wires=2)
    qml.RZ(params2, wires=0)
    qml.RZ(params2, wires=1)
    qml.RZ(params2, wires=2)


def fubini_ansatz4(params00, params_rest, wires=None):
    params01 = params_rest[0]
    params10 = params_rest[1]
    params11 = params_rest[2]
    qml.RY(fixed_pars[3], wires=0)
    qml.RY(fixed_pars[2], wires=1)
    qml.CNOT(wires=[0, 1])
    qml.CNOT(wires=[1, 2])
    qml.RY(fixed_pars[4], wires=0)
    qml.RX(params00, wires=0)
    qml.CNOT(wires=[0, 1])
    qml.RX(params01, wires=1)
    qml.RZ(params10, wires=1)
    qml.CNOT(wires=[0, 1])
    qml.RZ(params11, wires=1)


def fubini_ansatz5(params, wires=None):
    fubini_ansatz4(params[0], [params[0], params[1], params[1]], wires=wires)


def fubini_ansatz6(params, wires=None):
    fubini_ansatz4(params[0], [params[0], params[1], -params[1]], wires=wires)


def fubini_ansatz7(x, wires=None):
    qml.RX(fixed_pars[0], wires=0)
    qml.RX(x, wires=0)


def fubini_ansatz8(params, wires=None):
    params0 = params[0]
    params1 = params[1]
    qml.RX(fixed_pars[1], wires=[0])
    qml.RY(fixed_pars[3], wires=[0])
    qml.RZ(fixed_pars[2], wires=[0])
    qml.RX(fixed_pars[2], wires=[1])
    qml.RY(fixed_pars[2], wires=[1])
    qml.RZ(fixed_pars[4], wires=[1])
    qml.CNOT(wires=[0, 1])
    qml.RX(fixed_pars[0], wires=[0])
    qml.RY(fixed_pars[1], wires=[0])
    qml.RZ(fixed_pars[3], wires=[0])
    qml.RX(fixed_pars[1], wires=[1])
    qml.RY(fixed_pars[2], wires=[1])
    qml.RZ(fixed_pars[0], wires=[1])
    qml.CNOT(wires=[0, 1])
    qml.RX(params0, wires=[0])
    qml.RX(params0, wires=[1])
    qml.CNOT(wires=[0, 1])
    qml.RY(fixed_pars[4], wires=[1])
    qml.RY(params1, wires=[0])
    qml.RY(params1, wires=[1])
    qml.CNOT(wires=[0, 1])
    qml.RX(fixed_pars[2], wires=[1])


B = np.array(
    [
        [
            [0.73, 0.49, 0.04],
            [0.29, 0.45, 0.59],
            [0.64, 0.06, 0.26],
        ],
        [
            [0.93, 0.14, 0.46],
            [0.31, 0.83, 0.79],
            [0.25, 0.40, 0.16],
        ],
    ],
    requires_grad=True,
)
fubini_ansatze_tape = [fubini_ansatz0, fubini_ansatz1, fubini_ansatz7]
fubini_params_tape = [
    (np.array([0.3434, -0.7245345], requires_grad=True),),
    (B,),
    (-0.1735,),
]

fubini_ansatze = [
    fubini_ansatz0,
    fubini_ansatz1,
    fubini_ansatz2,
    fubini_ansatz3,
    fubini_ansatz4,
    fubini_ansatz5,
    fubini_ansatz6,
    fubini_ansatz7,
    fubini_ansatz8,
]

fubini_params = [
    (np.array([0.3434, -0.7245345], requires_grad=True),),
    (B,),
    (np.array([-0.1111, -0.2222], requires_grad=True),),
    (np.array([-0.1111, -0.2222, 0.4554], requires_grad=True),),
    (
        -0.1735,
        np.array([-0.1735, -0.2846, -0.2846], requires_grad=True),
    ),
    (np.array([-0.1735, -0.2846], requires_grad=True),),
    (np.array([-0.1735, -0.2846], requires_grad=True),),
    (-0.1735,),
    (np.array([-0.1111, 0.3333], requires_grad=True),),
]


def autodiff_metric_tensor(ansatz, num_wires):
    """Compute the metric tensor by full state vector
    differentiation via autograd."""
    dev = qml.device("default.qubit", wires=num_wires)

    @qml.qnode(dev)
    def qnode(*params):
        ansatz(*params, wires=dev.wires)
        return qml.state()

    def mt(*params):
        state = qnode(*params)
        rqnode = lambda *params: np.real(qnode(*params))
        iqnode = lambda *params: np.imag(qnode(*params))
        rjac = qml.jacobian(rqnode)(*params)
        ijac = qml.jacobian(iqnode)(*params)
        if isinstance(rjac, tuple):
            out = []
            for rc, ic in zip(rjac, ijac):
                c = rc + 1j * ic
                psidpsi = np.tensordot(np.conj(state), c, axes=([0], [0]))
                out.append(
                    np.real(
                        np.tensordot(np.conj(c), c, axes=([0], [0]))
                        - np.tensordot(np.conj(psidpsi), psidpsi, axes=0)
                    )
                )
            return tuple(out)

        jac = rjac + 1j * ijac
        psidpsi = np.tensordot(np.conj(state), jac, axes=([0], [0]))
        return np.real(
            np.tensordot(np.conj(jac), jac, axes=([0], [0]))
            - np.tensordot(np.conj(psidpsi), psidpsi, axes=0)
        )

    return mt


class TestAdjointMetricTensorTape:
    """Test the adjoint method for the metric tensor when calling it directly on
    a tape.
    """

    num_wires = 3

    @pytest.mark.parametrize("ansatz, params", zip(fubini_ansatze_tape, fubini_params_tape))
    def test_correct_output_tape_autograd(self, ansatz, params):
        """Test that the output is correct when using Autograd and
        calling the adjoint metric tensor directly on a tape."""
        expected = autodiff_metric_tensor(ansatz, self.num_wires)(*params)
        dev = qml.device("default.qubit.autograd", wires=self.num_wires)

        @qml.qnode(dev, interface="autograd")
        def circuit(*params):
            """Circuit with dummy output to create a QNode."""
            ansatz(*params, dev.wires)
            return qml.expval(qml.PauliZ(0))

        circuit(*params)
        mt = qml.adjoint_metric_tensor(circuit.qtape, dev)
        expected = qml.math.reshape(expected, qml.math.shape(mt))
        assert qml.math.allclose(mt, expected)

    @pytest.mark.skip("JAX does not support forward pass executiong of the metric tensor.")
    @pytest.mark.parametrize("ansatz, params", zip(fubini_ansatze_tape, fubini_params_tape))
    def test_correct_output_tape_jax(self, ansatz, params):
        """Test that the output is correct when using JAX and
        calling the adjoint metric tensor directly on a tape."""

        jax = pytest.importorskip("jax")
        from jax.config import config

        config.update("jax_enable_x64", True)

        expected = autodiff_metric_tensor(ansatz, self.num_wires)(*params)
        j_params = tuple(jax.numpy.array(p) for p in params)
        dev = qml.device("default.qubit.jax", wires=self.num_wires)

        @qml.qnode(dev, interface="jax")
        def circuit(*params):
            """Circuit with dummy output to create a QNode."""
            ansatz(*params, dev.wires)
            return qml.expval(qml.PauliZ(0))

        circuit(*j_params)
        mt = qml.adjoint_metric_tensor(circuit.qtape, dev)
        expected = qml.math.reshape(expected, qml.math.shape(mt))
        assert qml.math.allclose(mt, expected)

    @pytest.mark.parametrize("ansatz, params", zip(fubini_ansatze_tape, fubini_params_tape))
    def test_correct_output_tape_torch(self, ansatz, params):
        """Test that the output is correct when using Torch and
        calling the adjoint metric tensor directly on a tape."""

        torch = pytest.importorskip("torch")

        expected = autodiff_metric_tensor(ansatz, self.num_wires)(*params)
        t_params = tuple(torch.tensor(p, requires_grad=True) for p in params)
        dev = qml.device("default.qubit.torch", wires=self.num_wires)

        @qml.qnode(dev, interface="torch")
        def circuit(*params):
            """Circuit with dummy output to create a QNode."""
            ansatz(*params, dev.wires)
            return qml.expval(qml.PauliZ(0))

        circuit(*t_params)
        mt = qml.adjoint_metric_tensor(circuit.qtape, dev)
        expected = qml.math.reshape(expected, qml.math.shape(mt))
        assert qml.math.allclose(mt.detach().numpy(), expected)

    @pytest.mark.parametrize("ansatz, params", zip(fubini_ansatze_tape, fubini_params_tape))
    def test_correct_output_tape_tf(self, ansatz, params):
        """Test that the output is correct when using TensorFlow and
        calling the adjoint metric tensor directly on a tape."""

        tf = pytest.importorskip("tensorflow")

        expected = autodiff_metric_tensor(ansatz, self.num_wires)(*params)
        t_params = tuple(tf.Variable(p) for p in params)
        dev = qml.device("default.qubit.tf", wires=self.num_wires)

        @qml.qnode(dev, interface="tf")
        def circuit(*params):
            """Circuit with dummy output to create a QNode."""
            ansatz(*params, dev.wires)
            return qml.expval(qml.PauliZ(0))

        with tf.GradientTape() as t:
            circuit(*t_params)
            mt = qml.adjoint_metric_tensor(circuit.qtape, dev)
            expected = qml.math.reshape(expected, qml.math.shape(mt))
            assert qml.math.allclose(mt, expected)


class TestAdjointMetricTensorQNode:
    """Test the adjoint method for the metric tensor when calling it on
    a QNode.
    """

    num_wires = 3

    @pytest.mark.parametrize("ansatz, params", zip(fubini_ansatze, fubini_params))
    def test_correct_output_qnode_autograd(self, ansatz, params):
        """Test that the output is correct when using Autograd and
        calling the adjoint metric tensor on a QNode."""
        expected = autodiff_metric_tensor(ansatz, self.num_wires)(*params)
        dev = qml.device("default.qubit", wires=self.num_wires)

        @qml.qnode(dev, interface="autograd")
        def circuit(*params):
            """Circuit with dummy output to create a QNode."""
            ansatz(*params, dev.wires)
            return qml.expval(qml.PauliZ(0))

        mt = qml.adjoint_metric_tensor(circuit)(*params)

        if isinstance(mt, tuple):
            assert all(qml.math.allclose(_mt, _exp) for _mt, _exp in zip(mt, expected))
        else:
            assert qml.math.allclose(mt, expected)

    @pytest.mark.skip("JAX does not support forward pass executiong of the metric tensor.")
    @pytest.mark.parametrize("ansatz, params", zip(fubini_ansatze, fubini_params))
    def test_correct_output_qnode_jax(self, ansatz, params):
        """Test that the output is correct when using JAX and
        calling the adjoint metric tensor on a QNode."""

        jax = pytest.importorskip("jax")
        from jax.config import config

        config.update("jax_enable_x64", True)

        expected = autodiff_metric_tensor(ansatz, self.num_wires)(*params)
        j_params = tuple(jax.numpy.array(p) for p in params)
        dev = qml.device("default.qubit", wires=self.num_wires)

        @qml.qnode(dev, interface="jax")
        def circuit(*params):
            """Circuit with dummy output to create a QNode."""
            ansatz(*params, dev.wires)
            return qml.expval(qml.PauliZ(0))

        mt = qml.adjoint_metric_tensor(circuit)(*j_params)

        if isinstance(mt, tuple):
            assert all(qml.math.allclose(_mt, _exp) for _mt, _exp in zip(mt, expected))
        else:
            assert qml.math.allclose(mt, expected)

    @pytest.mark.parametrize("ansatz, params", zip(fubini_ansatze, fubini_params))
    def test_correct_output_qnode_torch(self, ansatz, params):
        """Test that the output is correct when using Torch and
        calling the adjoint metric tensor on a QNode."""

        torch = pytest.importorskip("torch")

        expected = autodiff_metric_tensor(ansatz, self.num_wires)(*params)
        t_params = tuple(torch.tensor(p, requires_grad=True, dtype=torch.float64) for p in params)
        dev = qml.device("default.qubit", wires=self.num_wires)

        @qml.qnode(dev, interface="torch")
        def circuit(*params):
            """Circuit with dummy output to create a QNode."""
            ansatz(*params, dev.wires)
            return qml.expval(qml.PauliZ(0))

        mt = qml.adjoint_metric_tensor(circuit)(*t_params)

        if isinstance(mt, tuple):
            assert all(qml.math.allclose(_mt, _exp) for _mt, _exp in zip(mt, expected))
        else:
            assert qml.math.allclose(mt, expected)

    @pytest.mark.parametrize("ansatz, params", zip(fubini_ansatze, fubini_params))
    def test_correct_output_qnode_tf(self, ansatz, params):
        """Test that the output is correct when using TensorFlow and
        calling the adjoint metric tensor on a QNode."""

        tf = pytest.importorskip("tensorflow")

        expected = autodiff_metric_tensor(ansatz, self.num_wires)(*params)
        t_params = tuple(tf.Variable(p, dtype=tf.float64) for p in params)
        dev = qml.device("default.qubit", wires=self.num_wires)

        @qml.qnode(dev, interface="tf")
        def circuit(*params):
            """Circuit with dummy output to create a QNode."""
            ansatz(*params, dev.wires)
            return qml.expval(qml.PauliZ(0))

        with tf.GradientTape() as t:
            mt = qml.adjoint_metric_tensor(circuit)(*t_params)

        if isinstance(mt, tuple):
            assert all(qml.math.allclose(_mt, _exp) for _mt, _exp in zip(mt, expected))
        else:
            assert qml.math.allclose(mt, expected)


@pytest.mark.skip(
    "Autodifferentiation of the adjoint method is not supported yet (Runtime problems)"
)
@pytest.mark.parametrize("ansatz, params", zip(fubini_ansatze, fubini_params))
class TestAdjointMetricTensorDifferentiability:
    """Test the differentiability of the adjoint method for the metric
    tensor when calling it on a QNode.
    """

    num_wires = 3

    def test_autograd(self, ansatz, params):
        """Test that the derivative is correct when using Autograd and
        calling the adjoint metric tensor on a QNode."""
        exp_fn = autodiff_metric_tensor(ansatz, self.num_wires)
        expected = qml.jacobian(exp_fn)(*params)
        dev = qml.device("default.qubit", wires=self.num_wires)

        @qml.qnode(dev, interface="autograd")
        def circuit(*params):
            """Circuit with dummy output to create a QNode."""
            ansatz(*params, dev.wires)
            return qml.expval(qml.PauliZ(0))

        mt = qml.jacobian(qml.adjoint_metric_tensor(circuit))(*params)

        if isinstance(mt, tuple):
            assert all(qml.math.allclose(_mt, _exp) for _mt, _exp in zip(mt, expected))
        else:
            assert qml.math.allclose(mt, expected)

    def test_correct_output_qnode_jax(self, ansatz, params):
        """Test that the derivative is correct when using JAX and
        calling the adjoint metric tensor on a QNode."""

        jax = pytest.importorskip("jax")
        from jax.config import config

        config.update("jax_enable_x64", True)

        expected = qml.jacobian(autodiff_metric_tensor(ansatz, self.num_wires))(*params)
        j_params = tuple(jax.numpy.array(p) for p in params)
        dev = qml.device("default.qubit", wires=self.num_wires)

        @qml.qnode(dev, interface="jax")
        def circuit(*params):
            """Circuit with dummy output to create a QNode."""
            ansatz(*params, dev.wires)
            return qml.expval(qml.PauliZ(0))

        mt = qml.adjoint_metric_tensor(circuit)(*j_params)

        if isinstance(mt, tuple):
            assert all(qml.math.allclose(_mt, _exp) for _mt, _exp in zip(mt, expected))
        else:
            assert qml.math.allclose(mt, expected)

    def test_correct_output_qnode_torch(self, ansatz, params):
        """Test that the derivative is correct when using Torch and
        calling the adjoint metric tensor on a QNode."""

        torch = pytest.importorskip("torch")

        expected = qml.jacobian(autodiff_metric_tensor(ansatz, self.num_wires))(*params)
        t_params = tuple(torch.tensor(p, requires_grad=True, dtype=torch.float64) for p in params)
        dev = qml.device("default.qubit", wires=self.num_wires)

        @qml.qnode(dev, interface="torch")
        def circuit(*params):
            """Circuit with dummy output to create a QNode."""
            ansatz(*params, dev.wires)
            return qml.expval(qml.PauliZ(0))

        mt = qml.adjoint_metric_tensor(circuit)(*t_params)

        if isinstance(mt, tuple):
            assert all(qml.math.allclose(_mt, _exp) for _mt, _exp in zip(mt, expected))
        else:
            assert qml.math.allclose(mt, expected)

    def test_correct_output_qnode_tf(self, ansatz, params):
        """Test that the derivative is correct when using TensorFlow and
        calling the adjoint metric tensor on a QNode."""

        tf = pytest.importorskip("tensorflow")

        expected = qml.jacobian(autodiff_metric_tensor(ansatz, self.num_wires))(*params)
        t_params = tuple(tf.Variable(p, dtype=tf.float64) for p in params)
        dev = qml.device("default.qubit", wires=self.num_wires)

        @qml.qnode(dev, interface="tf")
        def circuit(*params):
            """Circuit with dummy output to create a QNode."""
            ansatz(*params, dev.wires)
            return qml.expval(qml.PauliZ(0))

        with tf.GradientTape() as t:
            mt = qml.adjoint_metric_tensor(circuit)(*t_params)

        if isinstance(mt, tuple):
            assert all(qml.math.allclose(_mt, _exp) for _mt, _exp in zip(mt, expected))
        else:
            assert qml.math.allclose(mt, expected)


class TestErrors:
    """Test that errors are raised correctly."""

    def test_error_wrong_object_passed(self):
        """Test that an error is raised if neither a tape nor a QNode is passed."""

        def ansatz(x, y):
            qml.RX(x, wires=0)
            qml.RY(y, wires=1)

        dev = qml.device("default.qubit", wires=2)

        with pytest.raises(qml.QuantumFunctionError, match="The passed object is not a "):
            qml.adjoint_metric_tensor(ansatz, device=dev)

    def test_error_finite_shots(self):
        """Test that an error is raised if the device has a finite number of shots set."""
        with qml.tape.JacobianTape() as tape:
            qml.RX(0.2, wires=0)
            qml.RY(1.9, wires=1)
        dev = qml.device("default.qubit", wires=2, shots=1)

        with pytest.raises(ValueError, match="The adjoint method for the metric tensor"):
            qml.adjoint_metric_tensor(tape, device=dev)
