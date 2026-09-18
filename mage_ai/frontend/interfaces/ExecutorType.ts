export enum ExecutorTypeEnum {
  K8S = 'k8s',
  LOCAL_PYTHON = 'local_python',
}

export const EXECUTOR_TYPES = [
  ExecutorTypeEnum.LOCAL_PYTHON,
  ExecutorTypeEnum.K8S,
];
