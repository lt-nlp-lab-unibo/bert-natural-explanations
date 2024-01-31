from pathlib import Path
from typing import Tuple, Optional, Any, Iterable, List

import numpy as np
import pandas as pd

from cinnamon_core.core.data import FieldDict
from cinnamon_generic.components.data_loader import DataLoader
from cinnamon_generic.components.file_manager import FileManager


class IBMLoader(DataLoader):

    def __init__(
            self,
            **kwargs
    ):
        super().__init__(**kwargs)
        self.kb = None

    def load_kb(
            self,
            filepath: Path
    ) -> Iterable[str]:
        sentences = []

        with open(filepath, 'r') as f:
            for line in f:
                sentences.append(line)

        return sentences

    def load_data(
            self
    ):
        file_manager = FileManager.retrieve_component_instance(name='file_manager',
                                                               tags={'default'},
                                                               namespace='generic')
        df_path: Path = file_manager.dataset_directory.joinpath(self.name)
        if not df_path.exists():
            df_path.mkdir(parents=True)

        df_path = df_path.joinpath(f'dataset_{self.topics}.csv')
        df = pd.read_csv(df_path)

        kb_path = df_path.with_name(f'kb_{self.topics}.txt')
        self.kb = self.load_kb(filepath=kb_path)

        return df

    def get_splits(
            self
    ) -> Tuple[Optional[Any], Optional[Any], Optional[Any]]:
        df = self.load_data()

        return df[:self.samples_amount], None, None

    def parse(
            self,
            data: Optional[Any] = None,
    ) -> Optional[FieldDict]:

        if data is None:
            return data

        return_field = FieldDict()
        return_field.add(name='text',
                         value=data['Sentence'].values.tolist(),
                         type_hint=Iterable[str],
                         tags={'text'},
                         description='Text to classify')
        return_field.add(name='label',
                         value=data['C_Label'].values.tolist(),
                         type_hint=Iterable[str],
                         tags={'label'},
                         description='Claim label')
        return_field.add(name='kb',
                         value=self.kb,
                         type_hint=List[str],
                         tags={'metadata'},
                         description="Evidence texts")
        targets = data[f'evidence_targets'].values
        targets = [[int(item) for item in t.replace('[', '').replace(']', '').split(',')] if t != '[]' else [] for
                   t in targets]
        memory_targets = []
        for target_set in targets:
            target_mask = np.zeros((len(self.kb)))
            target_mask[target_set] = 1
            memory_targets.append(target_mask.tolist())
        memory_targets = np.array(memory_targets)
        return_field.add(name='memory_targets',
                         value=memory_targets,
                         tags={'metadata'},
                         description='Ground-truth memory target mask associated to sample.'
                                     'The targets are used by strong supervision to guide a model to'
                                     'correctly select explanations.')
        return return_field
