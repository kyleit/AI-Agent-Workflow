{{- define "msgbus-ws.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{- define "msgbus-ws.fullname" -}}
{{- default .Chart.Name .Values.fullnameOverride | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{- define "msgbus-ws.labels" -}}
app.kubernetes.io/name: {{ include "msgbus-ws.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
app: {{ include "msgbus-ws.name" . }}
{{- end -}}

{{- define "msgbus-ws.selectorLabels" -}}
app: {{ include "msgbus-ws.name" . }}
{{- end -}}

{{/* Name of the Secret that holds MSGBUS_TOKEN. */}}
{{- define "msgbus-ws.secretName" -}}
{{- if .Values.existingSecret -}}
{{- .Values.existingSecret -}}
{{- else -}}
{{- printf "%s-secret" (include "msgbus-ws.fullname" .) -}}
{{- end -}}
{{- end -}}

{{- define "msgbus-ws.image" -}}
{{- printf "%s:%s" .Values.image.repository (default .Chart.AppVersion .Values.image.tag) -}}
{{- end -}}
