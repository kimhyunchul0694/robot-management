// 상대 경로를 사용하여 내 컴퓨터 및 스마트폰 접속 모두 지원
const API_URL = "/api/students";

// 페이지 로드 시 학생 목록 불러오기
document.addEventListener("DOMContentLoaded", () => {
    fetchStudents();
});

// 1. 전체 학생 목록 조회
async function fetchStudents() {
    try {
        const response = await fetch(API_URL);
        if (!response.ok) throw new Error("데이터 조회 실패");

        const students = await response.json();
        renderStudents(students);
        updateSummary(students);
    } catch (error) {
        console.error("학생 목록 로딩 중 오류:", error);
    }
}

// 2. 학생 목록 화면에 출력
function renderStudents(students) {
    const listTable = document.getElementById("student-list");
    listTable.innerHTML = "";

    students.forEach(student => {
        const tr = document.createElement("tr");
        tr.innerHTML = `
            <td>${student.id}</td>
            <td>${student.name}</td>
            <td>${student.grade}</td>
            <td>
                <select onchange="updateAttendance(${student.id}, this.value)">
                    <option value="출석" ${student.attendance === '출석' ? 'selected' : ''}>출석</option>
                    <option value="결석" ${student.attendance === '결석' ? 'selected' : ''}>결석</option>
                    <option value="조퇴" ${student.attendance === '조퇴' ? 'selected' : ''}>조퇴</option>
                </select>
            </td>
            <td>
                <button class="btn-delete" onclick="deleteStudent(${student.id})">삭제</button>
                <button style="padding: 3px 8px; font-size: 12px; background: #FF9800;" onclick="fillAILogForm('${student.name}')">일지 작성</button>
            </td>
        `;
        listTable.appendChild(tr);
    });
}

// 3. 통계 대시보드 업데이트
function updateSummary(students) {
    const total = students.length;
    const present = students.filter(s => s.attendance === "출석").length;
    const absent = total - present;

    document.getElementById("total-count").innerText = total;
    document.getElementById("present-count").innerText = present;
    document.getElementById("absent-count").innerText = absent;
}

// 4. 학생 추가
async function addStudent() {
    const nameInput = document.getElementById("student-name");
    const gradeInput = document.getElementById("student-grade");

    if (!nameInput.value || !gradeInput.value) {
        alert("이름과 학년을 모두 입력해 주세요.");
        return;
    }

    try {
        const response = await fetch(API_URL, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                name: nameInput.value,
                grade: gradeInput.value
            })
        });

        if (response.ok) {
            nameInput.value = "";
            gradeInput.value = "";
            fetchStudents();
        } else {
            alert("학생 등록에 실패했습니다.");
        }
    } catch (error) {
        console.error("학생 추가 오류:", error);
    }
}

// 5. 출석 상태 변경
async function updateAttendance(studentId, newStatus) {
    try {
        await fetch(`${API_URL}/${studentId}`, {
            method: "PUT",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ attendance: newStatus })
        });
        fetchStudents();
    } catch (error) {
        console.error("출석 변경 오류:", error);
    }
}

// 6. 학생 삭제
async function deleteStudent(studentId) {
    if (!confirm("정말 이 학생을 삭제하시겠습니까?")) return;

    try {
        await fetch(`${API_URL}/${studentId}`, {
            method: "DELETE"
        });
        fetchStudents();
    } catch (error) {
        console.error("학생 삭제 오류:", error);
    }
}

// 7. 학생 목록에서 '일지 작성' 버튼 클릭 시 이름을 AI 폼으로 전달
function fillAILogForm(studentName) {
    document.getElementById("log-student-name").value = studentName;
    document.getElementById("log-topic").focus();
}

// 8. 10차 미션: Gemini AI 수업일지 생성 호출
async function generateAILog() {
    const studentName = document.getElementById("log-student-name").value;
    const topic = document.getElementById("log-topic").value;
    const performance = document.getElementById("log-performance").value;
    const resultDiv = document.getElementById("log-result");

    if (!studentName || !topic) {
        alert("학생 이름과 수업 주제를 입력해 주세요.");
        return;
    }

    resultDiv.innerText = "⏳ AI가 수업일지를 작성하고 있습니다. 잠시만 기다려 주세요...";

    try {
        const response = await fetch("/api/generate-log", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                student_name: studentName,
                today_topic: topic,
                performance: performance
            })
        });

        if (!response.ok) {
            throw new Error("서버 응답 오류");
        }

        const data = await response.json();
        resultDiv.innerText = data.log;
    } catch (error) {
        console.error("AI 일지 생성 오류:", error);
        resultDiv.innerText = "❌ 일지 생성에 실패했습니다. Gemini API 키 및 서버 터미널 로그를 확인하세요.";
    }
}

async function generateNotice() {
    const studentName = document.getElementById("log-student-name").value;
    const todayTopic = document.getElementById("log-topic").value;
    const performance = document.getElementById("log-performance").value;
    const resultDiv = document.getElementById("notice-result");

    if (!studentName || !todayTopic) {
        alert("학생 이름과 수업 주제를 먼저 입력해 주세요!");
        return;
    }

    resultDiv.innerText = "⏳ AI가 학부모님께 보낼 알림장을 작성 중입니다...";

    try {
        const response = await fetch("/api/generate-notice", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                student_name: studentName,
                today_topic: todayTopic,
                performance: performance
            })
        });

        const data = await response.json();

        if (response.ok) {
            resultDiv.innerText = data.notice;
        } else {
            resultDiv.innerText = "❌ 알림장 생성 실패: " + (data.detail || "오류가 발생했습니다.");
        }
    } catch (error) {
        console.error("Error:", error);
        resultDiv.innerText = "❌ 서버와 통신할 수 없습니다.";
    }
}
