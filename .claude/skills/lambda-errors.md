# Skill: Lambda Error Monitoring

Monitoring des erreurs Lambda via AWS CloudWatch.

## Fonctions Lambda (prod)

| Fonction | Description |
|----------|-------------|
| `etl-prod-*` | Fonctions principales de traitement |

## Lister les fonctions

```bash
aws lambda list-functions --query 'Functions[].FunctionName' --output table
```

## Consulter les logs d'erreurs

Les logs Lambda sont dans CloudWatch Logs sous `/aws/lambda/{function-name}`.

### Erreurs récentes (dernière heure)

```bash
aws logs filter-log-events \
  --log-group-name "/aws/lambda/FUNCTION_NAME" \
  --start-time $(date -v-1H +%s000) \
  --filter-pattern "ERROR"
```

### Rechercher un pattern spécifique

```bash
aws logs filter-log-events \
  --log-group-name "/aws/lambda/FUNCTION_NAME" \
  --start-time $(date -v-24H +%s000) \
  --filter-pattern "?ERROR ?Exception ?error ?FATAL"
```

### Logs des dernières invocations

```bash
aws logs tail "/aws/lambda/FUNCTION_NAME" --since 1h --follow
```

## Métriques d'erreurs

### Erreurs sur les dernières 24h

```bash
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Errors \
  --dimensions Name=FunctionName,Value=FUNCTION_NAME \
  --start-time $(date -v-24H -u +%Y-%m-%dT%H:%M:%SZ) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%SZ) \
  --period 3600 \
  --statistics Sum
```

### Invocations vs erreurs (comparaison)

```bash
# Invocations
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Invocations \
  --dimensions Name=FunctionName,Value=FUNCTION_NAME \
  --start-time $(date -v-24H -u +%Y-%m-%dT%H:%M:%SZ) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%SZ) \
  --period 3600 \
  --statistics Sum

# Erreurs
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Errors \
  --dimensions Name=FunctionName,Value=FUNCTION_NAME \
  --start-time $(date -v-24H -u +%Y-%m-%dT%H:%M:%SZ) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%SZ) \
  --period 3600 \
  --statistics Sum
```

### Timeouts (durée max)

```bash
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Duration \
  --dimensions Name=FunctionName,Value=FUNCTION_NAME \
  --start-time $(date -v-24H -u +%Y-%m-%dT%H:%M:%SZ) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%SZ) \
  --period 3600 \
  --statistics Maximum
```

## Exemples

```bash
# Voir toutes les erreurs de toutes les fonctions etl-prod
for fn in $(aws lambda list-functions --query 'Functions[?starts_with(FunctionName, `etl-prod`)].FunctionName' --output text); do
  echo "=== $fn ==="
  aws logs filter-log-events \
    --log-group-name "/aws/lambda/$fn" \
    --start-time $(date -v-1H +%s000) \
    --filter-pattern "ERROR" \
    --max-items 5 2>/dev/null || echo "No log group"
done

# Erreurs avec stack trace
aws logs filter-log-events \
  --log-group-name "/aws/lambda/FUNCTION_NAME" \
  --start-time $(date -v-6H +%s000) \
  --filter-pattern "Traceback"
```

## Prérequis

- AWS CLI configuré avec les credentials appropriés
- Permissions: `logs:FilterLogEvents`, `logs:DescribeLogGroups`, `cloudwatch:GetMetricStatistics`, `lambda:ListFunctions`
