helm repo add newrelic https://helm-charts.newrelic.com && \
kubectl create namespace newrelic ; helm install newrelic-bundle newrelic/nri-bundle \
 --set global.licenseKey=$NEWRELIC_LICENSE_KEY \
 --set global.cluster=dg-k8s-sandbox \
 --namespace=newrelic \
 --set newrelic-infrastructure.privileged=true \
 --set ksm.enabled=true \
 --set prometheus.enabled=true \
 --set kubeEvents.enabled=true \
 --set logging.enabled=true 

