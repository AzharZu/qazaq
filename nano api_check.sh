#!/bin/bash

BASE="http://127.0.0.1:8000"
COOKIE_JAR="cookies.txt"

divider() {
    echo "------------------------------------------------------------"
}

section() {
    divider
    echo "### $1"
    divider
}

run() {
    echo "▶ $1"
    shift
    curl -s -b $COOKIE_JAR -c $COOKIE_JAR "$@" | jq
    echo ""
}

echo ""
echo "🔥 STARTING QAZAQ API CHECK"
echo ""

# 1. HEALTH
section "HEALTH CHECK"
curl -s $BASE/ | head -c 200
echo ""

# 2. LOGIN (ADMIN)
section "LOGIN AS ADMIN"
curl -s -c $COOKIE_JAR -X POST $BASE/api/auth/login \
    -H "Content-Type: application/json" \
    -d '{"email":"admin@example.com","password":"admin123"}' | jq
echo ""

# 3. COURSES
section "GET /api/courses"
run "List Courses" "$BASE/api/courses"

# 4. COURSE DETAIL
section "GET /api/courses/id/1"
run "Course #1 Detail" "$BASE/api/courses/id/1"

# 5. LESSON DETAIL
section "GET /api/lessons/1"
run "Lesson #1 Detail" "$BASE/api/lessons/1"

# 6. PROGRESS
section "GET /api/progress"
run "User Progress" "$BASE/api/progress"

# 7. VOCABULARY LIST
section "GET /api/vocabulary"
run "Vocabulary List" "$BASE/api/vocabulary"

# 8. VOCABULARY GAME ROUND
section "GET /api/vocabulary/game?mode=multiple_choice"
run "Vocabulary MC Round" "$BASE/api/vocabulary/game?mode=multiple_choice"

# 9. VOCABULARY CHECK (Mock word_id=1)
section "POST /api/vocabulary/check"
curl -s -b $COOKIE_JAR -X POST $BASE/api/vocabulary/check \
    -H "Content-Type: application/json" \
    -d '{"mode":"mc","word_id":1,"answer":"test"}' | jq
echo ""

# 10. PLACEMENT TEST
section "GET /api/placement/start"
run "Placement Start" "$BASE/api/placement/start"

section "GET /api/placement/next"
run "Placement Next" "$BASE/api/placement/next"

# 11. CHECK IF AUTOCHECKER ROUTE EXISTS
section "CHECK AUTOCHECKER ROUTE"
curl -s "$BASE/api/autochecker/ping" | jq
echo ""

echo ""
echo "🔥 API CHECK COMPLETE"
divider