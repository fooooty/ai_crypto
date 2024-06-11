library('stringr')
library('glmnet')

# 계수를 추출하는 함수 정의
extract <- function(o, s) { 
  index <- which(coef(o, s) != 0) 
  data.frame(name=rownames(coef(o))[index], coef=coef(o, s)[index]) 
}

options(scipen=999)

# args 수동 설정
args <- c('2024-05-01T00:00:00', '2024-05-01T23:59:00', 'upbit', 'BTC', 'mid5')

# 파일 이름 생성
filtered = paste(args[1], args[2], args[3], args[4], 'filtered-5-2', args[5], sep="-")
model_file = paste(args[2], args[3], args[4], args[5], 'lasso-5s-2std', sep='-')

# 파일 이름에서 콜론 제거
filtered <- str_remove_all(filtered, ":")
model_file <- str_remove_all(model_file, ":")

# CSV 파일 경로 설정
filtered_path <- "/Users/sonjiyeon/Desktop/2024-05-01T000000-2024-05-01T235900-upbit-BTC-filtered-5-2-mid5.csv"
# 결과 파일 경로 설정
model_file = paste("~/Desktop/", model_file, ".csv", sep="") 

# 경로 출력 확인
message("Filtered path: ", filtered_path)
message("Model file path: ", model_file)

# 현재 작업 디렉토리 확인
message("Current working directory: ", getwd())

# CSV 파일 읽기
filtered = read.csv(filtered_path)

# mid_price의 표준 편차 계산 및 출력
mid_std = sd(filtered$mid_price)
message("Standard deviation of mid_price: ", round(mid_std, 0))

# mid_price와 timestamp 열을 제외한 데이터 프레임 생성
filtered_no_time_mid = subset(filtered, select = -c(mid_price, timestamp))

# 종속 변수와 독립 변수 설정
y = filtered_no_time_mid$return  # 종속 변수: 수익률
x = subset(filtered_no_time_mid, select = -c(return))  # 독립 변수: 수익률을 제외한 나머지 변수들

# 독립 변수를 행렬로 변환
x <- as.matrix(x)

# LASSO 모델 교차 검증
cv_fit <- cv.glmnet(x = x, y = y, alpha = 1, intercept = FALSE, lower.limits = 0, nfolds = 5) # lasso

# 최종 모델 학습
fit <- glmnet(x = x, y = y, alpha = 1, lambda = cv_fit$lambda.1se, intercept = FALSE, lower.limits = 0)

# 계수 추출 및 전치
df <- extract(fit, s = 0.1)
df <- t(df)

# 결과를 CSV 파일로 저장
write.table(df, file = model_file, sep = ",", col.names = FALSE, row.names = FALSE, quote = FALSE)

message("Results saved to: ", model_file)
