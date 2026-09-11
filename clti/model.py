"""Fitted, batch-stable anomaly scoring with local feature-deviation explanations."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any
import numpy as np
FEATURE_NAMES=["log_total_input","log_fee_rate","fan_in","fan_out","output_concentration","peel_disparity","entity_tx_count","entity_peer_diversity","observation_count","observer_count","peer_count","network_confidence","coinjoin_warning"]
@dataclass
class ModelOutput:
    percentiles:np.ndarray;contributions:list[list[tuple[str,float]]];model_name:str
class ExplainableAnomalyModel:
    def __init__(self,random_state=42):self.random_state=random_state;self.median=None;self.scale=None;self.baseline_scores=None;self.model=None;self.model_name="RobustDeviationModel"
    def fit(self,rows):
        x=self._matrix(rows)
        if len(x)<10:raise ValueError("At least 10 baseline transactions are required")
        self.median=np.median(x,axis=0);mad=np.median(np.abs(x-self.median),axis=0);self.scale=np.where(mad>1e-9,1.4826*mad,np.std(x,axis=0));self.scale=np.where(self.scale>1e-9,self.scale,1.0)
        try:
            from sklearn.ensemble import IsolationForest
            self.model=IsolationForest(n_estimators=200,contamination="auto",random_state=self.random_state,n_jobs=1);self.model.fit(x);self.baseline_scores=-self.model.decision_function(x);self.model_name="IsolationForest-200"
        except ImportError:self.baseline_scores=self._robust_scores(x)
        self.baseline_scores=np.sort(self.baseline_scores);return self
    def score(self,rows):
        if self.median is None:raise RuntimeError("Model must be fitted before scoring")
        x=self._matrix(rows);raw=-self.model.decision_function(x) if self.model is not None else self._robust_scores(x)
        pct=np.array([100*np.searchsorted(self.baseline_scores,v,side="right")/len(self.baseline_scores) for v in raw]);z=np.abs((x-self.median)/self.scale);con=[]
        for values in z:
            order=np.argsort(values)[::-1][:3];total=float(values[order].sum()) or 1.0;con.append([(FEATURE_NAMES[i],round(float(values[i]/total),3)) for i in order])
        return ModelOutput(np.round(pct,1),con,self.model_name)
    def _matrix(self,rows):return np.asarray([[float(r.get(n,0)) for n in FEATURE_NAMES] for r in rows],dtype=float)
    def _robust_scores(self,x):
        z=np.abs((x-self.median)/self.scale);return np.mean(np.sort(z,axis=1)[:,-min(5,z.shape[1]):],axis=1)
