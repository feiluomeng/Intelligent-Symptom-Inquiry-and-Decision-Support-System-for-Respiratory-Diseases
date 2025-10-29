<template>
  <div class="page-layout">
    <div class="diagnosis-system">
      <h1>Respiratory Disease Diagnosis</h1>
      <el-form class="diagnosis-form">
        <div class="form-item">
          <label for="symptom">Symptom Description</label>
          <el-input id="symptom" v-model="form.symptom" placeholder="e.g. cough, fever" maxlength="100" />
        </div>
        <div class="form-item">
          <label for="diseaseType">Disease Type</label>
          <el-select id="diseaseType" v-model="form.diseaseType" clearable multiple collapse-tags>
            <el-option value="Cough">Cough</el-option>
            <el-option value="Fatigue">Fatigue</el-option>
            <el-option value="Fever">Fever</el-option>
            <el-option value="Difficulty Breathing">Difficulty Breathing</el-option>
          </el-select>
        </div>
        <el-button type="primary" class="submit-button" @click="fetchMedline"
          v-loading.fullscreen.lock="form.fullscreenLoading">Diagnose</el-button>
      </el-form>
      <div class="result" v-if="form.diagnosisList.length">
        <h2>Diagnosis Result</h2>
        <!-- <p>{{ diagnosisResult }}</p> -->
        <div class="result" v-if="form.diagnosisList.length">
          <el-collapse>
            <el-collapse-item v-for="(item, idx) in form.diagnosisList" :key="idx">
              <template #title>
                <span v-html="item.title || item.word"></span>
              </template>
              <div class="diagnosis-card">
                <div class="diagnosis-title" v-html="item.title || item.word"></div>
                <div class="diagnosis-summary" v-html="item.FullSummary"></div>
                <el-link :href="item.url" target="_blank" type="primary">MedlinePlus details</el-link>
              </div>
            </el-collapse-item>
          </el-collapse>
        </div>

      </div>
      <el-dialog v-model="form.dialogVisibleTwo" title="Tips" draggable>
        <p>There are no search results. Please try again later.</p>
        <template #footer>
          <span class="dialog-footer">
            <el-button type="primary" @click="form.dialogVisibleTwo = false">
              Confirm
            </el-button>
          </span>
        </template>
      </el-dialog>
      <el-dialog v-model="form.dialogVisible" title="Tips" draggable>
        <p>{{ form.tips }}</p>
        <template #footer>
          <span class="dialog-footer">
            <el-button type="primary" @click="form.dialogVisible = false">
              Confirm
            </el-button>
          </span>
        </template>
      </el-dialog>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';

const form = ref({
  symptom: '',
  tips: '',
  diseaseType: [] as string[],
  dialogVisible: ref(false),
  dialogVisibleTwo: ref(false),
  respiratoryDiseaseSymptomsMap: {
    "Allergic Rhinitis": ["Cough", "Fatigue"],
    "Asthma": ["Fever", "Cough", "Difficulty Breathing"],
    "Bronchitis": ["Fever", "Cough", "Fatigue", "Difficulty Breathing"],
    "Chronic Obstructive Pulmonary Disease (COPD)": ["Fever", "Cough", "Fatigue", "Difficulty Breathing"],
    "Common Cold": ["Fever", "Fatigue"],
    "Cystic Fibrosis": ["Fatigue", "Difficulty Breathing"],
    "Influenza": ["Fever", "Cough", "Fatigue", "Difficulty Breathing"],
    "Lung Cancer": ["Fever", "Fatigue"],
    "Pneumocystis Pneumonia (PCP)": ["Fever", "Cough", "Fatigue"],
    "Pneumonia": ["Fever", "Cough", "Fatigue", "Difficulty Breathing"],
    "Pneumothorax": ["Fatigue", "Difficulty Breathing"],
    "Sinusitis": ["Cough", "Fatigue"],
    "Sleep Apnea": ["Fever", "Fatigue", "Difficulty Breathing"],
    "Tonsillitis": ["Fever", "Cough", "Fatigue"],
    "Tuberculosis": ["Fever", "Cough", "Fatigue", "Difficulty Breathing"]
  },
  diagnosisList: ref<any[]>([]),
  fullscreenLoading: ref(false)

});

// 匹配函数
function matchDisease(symptoms: string[]): string[] {
  const matchedDiseases: string[] = [];

  // 遍历所有疾病
  for (const [disease, requiredSymptoms] of Object.entries(form.value.respiratoryDiseaseSymptomsMap)) {
    // 检查症状是否完全匹配
    const isMatch = requiredSymptoms.every(symptom =>
      symptoms.includes(symptom)
    );

    if (isMatch) {
      matchedDiseases.push(disease);
    }
  }

  return matchedDiseases;
}

async function fetchMedline() {
  console.log(form.value.symptom, form.value.diseaseType, form.value.diseaseType.length, '9999');

  if (!form.value.symptom && form.value.diseaseType.length === 0) {
    form.value.tips = 'Please enter a symptom or select a disease type.';
    form.value.dialogVisible = true;
    return;
  }
  if (form.value.symptom && form.value.diseaseType.length > 0) {
    form.value.tips = 'You can only choose to input text or select multiple options.';
    form.value.dialogVisible = true;
    return;
  }
  if (form.value.symptom.trim() && form.value.diseaseType.length === 0) {
    // input
    try {
      form.value.fullscreenLoading = true;
      const res = await fetch('http://127.0.0.1:5000/api/search', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ symptom: form.value.symptom, searchType: '1' })
      });
      const data = await res.json();
      console.log('MedlinePlus返回:', data);
      form.value.diagnosisList = data.results || [];
      form.value.fullscreenLoading = false;
      if (form.value.diagnosisList.length === 0) {
        form.value.dialogVisibleTwo = true;
        form.value.symptom = '';
      }
    } catch (e) {
      form.value.diagnosisList = [];
      form.value.dialogVisibleTwo = true;
      form.value.symptom = '';
      form.value.fullscreenLoading = false;
    }
  } else {
    // options
    try {
    debugger
      form.value.fullscreenLoading = true;
      let diseaseType = matchDisease(form.value.diseaseType);
      const res = await fetch('http://127.0.0.1:5000/api/search', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ symptom: diseaseType, searchType: '2' })
      });
      const data = await res.json();
      console.log('MedlinePlus返回:', data);
      form.value.fullscreenLoading = false;
      form.value.diagnosisList = data.results || [];
      if (form.value.diagnosisList.length === 0) {
        form.value.dialogVisibleTwo = true;
        form.value.diseaseType = [];
      }
      // diagnosisResult.value = null; // 可选，隐藏原来的字符串展示
    } catch (e) {
      form.value.diagnosisList = [];
      form.value.dialogVisibleTwo = true;
      form.value.diseaseType = [];
      form.value.fullscreenLoading = false;
    }
  }

}

// // 只监听疾病类型下拉框变化
// watch(() => form.value.diseaseType, (val) => {
//   if (val) {
//     fetchMedline(val);
//   }
// });

// function handleSubmit() {
//   let result = 'Preliminary diagnosis: ';
//   if (form.value.symptom) {
//     result += `Symptom: "${form.value.symptom}"; `;
//   }
//   if (form.value.diseaseType) {
//     result += `Possible disease type: "${form.value.diseaseType}"; `;
//   }
//   result += 'Please consult a doctor for further advice.';
//   diagnosisResult.value = result;
// }
</script>

<style scoped>
.page-layout {
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 20px;
  background: linear-gradient(135deg, #e3f2fd, #bbdefb);
  min-height: 100vh;
}

.diagnosis-system {
  max-width: 50%;
  width: 100%;
  padding: 30px;
  background: #fff;
  border-radius: 16px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
  transition: transform 0.3s, box-shadow 0.3s;
}

.diagnosis-system:hover {
  transform: translateY(-4px);
  box-shadow: 0 6px 20px rgba(0, 0, 0, 0.15);
}

.diagnosis-system h1 {
  text-align: center;
  margin-bottom: 20px;
  color: #007bff;
  font-size: 2rem;
  font-weight: bold;
  text-shadow: 0 2px 4px rgba(0, 123, 255, 0.2);
}

.form-item {
  margin-bottom: 20px;
}

.form-item label {
  display: block;
  font-size: 1rem;
  font-weight: bold;
  color: #333;
  margin-bottom: 8px;
}

.form-item input,
.form-item select {
  width: 100%;
  font-size: 1rem;
  padding: 10px;
  border-radius: 8px;
  border: 1.5px solid #bcdffb;
  box-shadow: 0 2px 8px rgba(0, 123, 255, 0.1);
  transition: box-shadow 0.3s, border-color 0.3s;
}

.form-item input:focus,
.form-item select:focus {
  box-shadow: 0 0 8px rgba(0, 198, 255, 0.4);
  border-color: #00c6ff;
}

.submit-button {
  width: 100%;
  padding: 14px 0;
  font-size: 1rem;
  font-weight: bold;
  border-radius: 8px;
  background: linear-gradient(90deg, #2196f3 0%, #00c6ff 100%);
  color: #fff;
  box-shadow: 0 2px 8px rgba(33, 150, 243, 0.2);
  border: none;
  margin-top: 10px;
  transition: background 0.2s, transform 0.2s;
}

.submit-button:hover {
  background: linear-gradient(90deg, #1565c0 0%, #0096c7 100%);
  transform: translateY(-2px) scale(1.04);
}

.result {
  margin-top: 20px;
  padding: 20px;
  border: 1px solid #007bff;
  border-radius: 8px;
  background: #f0f8ff;
  color: #333;
  font-size: 1rem;
  box-shadow: 0 2px 8px rgba(0, 123, 255, 0.2);
}

.diagnosis-card {
  margin-bottom: 10px;
}

.diagnosis-title {
  font-size: 1.1rem;
  font-weight: bold;
  color: #1565c0;
  margin-bottom: 8px;
}

.diagnosis-summary {
  margin-bottom: 8px;
  color: #333;
  font-size: 0.98rem;
}
</style>
