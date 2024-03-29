from typing import Type, Dict

import torch as th

from cinnamon_core.core.configuration import C
from cinnamon_core.core.registry import Registry, register, RegistrationKey
from cinnamon_generic.configurations.model import NetworkConfig
from components.model import HFBaseline, HFMANN
from configurations.model import MemoryNetworkConfig


class HFBaselineConfig(NetworkConfig):

    @classmethod
    def get_default(
            cls: Type[C]
    ) -> C:
        config = super().get_default()

        config.epochs = 50
        config.add(name='hf_model_name',
                   variants=['distilbert-base-uncased'],
                   is_required=True,
                   description="HugginFace's model card.")
        config.add(name='freeze_hf',
                   value=False,
                   allowed_range=lambda value: value in [False, True],
                   type_hint=bool,
                   description='If enabled, the HF model weights are freezed.')
        config.add(name='num_classes',
                   value=2,
                   type_hint=int,
                   description='Number of classification classes.',
                   tags={'model'},
                   is_required=True)
        config.add(name='optimizer_class',
                   value=th.optim.Adam,
                   is_required=True,
                   tags={'model'},
                   description='Optimizer to use for network weights update')
        config.add(name='optimizer_args',
                   value={
                       "lr": 5e-06,
                       "weight_decay": 1e-05
                   },
                   type_hint=Dict,
                   tags={'model'},
                   description="Arguments for creating the network optimizer")
        config.add(name='dropout_rate',
                   value=0.20,
                   type_hint=float,
                   description='Dropout rate for dropout layer')

        return config


class HFMANNConfig(MemoryNetworkConfig):

    @classmethod
    def get_default(
            cls: Type[C]
    ) -> C:
        config = super().get_default()

        # Note: we have to define an API for merging configurations
        for key, value in HFBaselineConfig.get_default().items():
            if key == 'conditions':
                value.value.update(config[key])
            config[key] = value

        config.lookup_weights = [
            32
        ]
        config.get('kb_sampler').variants = [
            RegistrationKey(name='sampler',
                            tags={'uniform'},
                            namespace='nle/ibm'),
            RegistrationKey(name='sampler',
                            tags={'attention'},
                            namespace='nle/ibm'),
            RegistrationKey(name='sampler',
                            tags={'gain'},
                            namespace='nle/ibm'),
        ]
        config.ss_margin = 0.5
        config.get('ss_coefficient').variants = [0.0, 1.0]

        return config


@register
def register_models():
    Registry.add_and_bind_variants(config_class=HFBaselineConfig,
                                   component_class=HFBaseline,
                                   name='model',
                                   tags={'hf', 'baseline'},
                                   namespace='nle/ibm')

    Registry.add_and_bind_variants(config_class=HFMANNConfig,
                                   component_class=HFMANN,
                                   name='model',
                                   tags={'hf', 'memory'},
                                   namespace='nle/ibm')