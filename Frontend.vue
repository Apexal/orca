<template>
  <div class="page">
    <h1>ORCA</h1>

    <input type="text" placeholder="CRNs" v-model.trim="crns" />
    <div class="course-sections">
      <div
        class="course-section"
        v-for="section in courseSections"
        :key="section.crn"
      >
        <h2>
          {{ section.course_subject_prefix }}-{{ section.course_number }}
          {{ section.course_title }}
        </h2>
        <h3>
          Section {{ section.section_id }}
          <span v-if="section.instruction_method"
            >({{ section.instruction_method }})</span
          >
        </h3>

        <h4>
          {{ section.credits.join("/") }} credits - {{ section.enrollments }}/{{
            section.max_enrollments
          }}
          seats taken
        </h4>

        <p>
          <a :href="section.textbooks_url" target="_blank">Textbooks URL</a>
        </p>

        <table class="section-periods">
          <thead>
            <tr>
              <th>Class Type</th>
              <th>Days</th>
              <th>Start Time</th>
              <th>End Time</th>
              <th>Instructors</th>
              <th>Location</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(period, index) in section.periods" :key="index">
              <td>{{ period.class_type }}</td>
              <td>{{ period.days.join(", ") }}</td>
              <td>{{ period.start_time || "TBA" }}</td>
              <td>{{ period.end_time || "TBA" }}</td>
              <td>{{ period.instructors.join(",") }}</td>
              <td>{{ period.location || "TBA" }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
    <button @click="fetchCourseSections">Fetch</button>
  </div>
</template>

<script>
export default {
  name: "Frontend",
  data() {
    return {
      crns: "",
      courseSections: [],
    };
  },
  computed: {
    urlSearchParams() {
      const usp = new URLSearchParams();
      if (this.crns) {
        for (const crn of this.crns.split(",")) {
          usp.append("crns", crn.trim());
        }
      }
      return usp;
    },
  },
  methods: {
    fetchCourseSections() {
      fetch(
        "http://localhost:8000/202101/sections?" +
          this.urlSearchParams.toString()
      )
        .then((response) => response.json())
        .then((data) => {
          this.courseSections = data;
        })
        .catch(alert);
    },
  },
};
</script>

<style>
.course-section {
  padding: 1em;
  border: 2px solid #222;
}
</style>