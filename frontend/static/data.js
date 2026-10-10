/* Sample Taiwan tourism data — placeholder/realistic names */
window.TAIWAN_DATA = {
  destinations: ["台北", "新北", "桃園", "新竹", "台中", "台南", "高雄", "宜蘭", "花蓮", "台東", "南投", "嘉義", "屏東"],
  popularDests: ["台北", "台中", "台南", "高雄", "花蓮", "宜蘭"],

  itinerary_台北_5天: [
    // Day 1
    [
      { id:"s1", name:"台北 101", category:"地標", catLabel:"地標", time:"09:30", duration:"2 hr", price:600, transport:{ mode:"捷運", time:"22 分鐘", cost:25 }, tags:["觀景台","購物"], thumb:"🏙️" },
      { id:"s2", name:"鼎泰豐 信義店", category:"食物", catLabel:"美食", time:"12:00", duration:"1.5 hr", price:850, transport:{ mode:"步行", time:"5 分鐘", cost:0 }, tags:["小籠包"], thumb:"🥟", catCls:"stop__category--food" },
      { id:"s3", name:"四四南村", category:"文化", catLabel:"文化", time:"14:30", duration:"1.5 hr", price:0, transport:{ mode:"步行", time:"8 分鐘", cost:0 }, tags:["眷村","散步"], thumb:"🏘️" },
      { id:"s4", name:"象山步道", category:"自然", catLabel:"自然", time:"16:30", duration:"2 hr", price:0, transport:{ mode:"捷運", time:"15 分鐘", cost:25 }, tags:["夕陽","健行"], thumb:"⛰️" },
    ],
    // Day 2
    [
      { id:"s5", name:"故宮博物院", category:"文化", catLabel:"文化", time:"09:00", duration:"3 hr", price:350, transport:{ mode:"公車", time:"40 分鐘", cost:30 }, tags:["國寶"], thumb:"🏛️" },
      { id:"s6", name:"士林夜市", category:"食物", catLabel:"夜市", time:"17:00", duration:"2.5 hr", price:600, transport:{ mode:"捷運", time:"20 分鐘", cost:25 }, tags:["小吃"], thumb:"🍢", catCls:"stop__category--food" },
      { id:"s7", name:"圓山大飯店", category:"住宿", catLabel:"住宿", time:"22:00", duration:"夜宿", price:3200, transport:{ mode:"計程車", time:"12 分鐘", cost:180 }, tags:["經典"], thumb:"🏨", catCls:"stop__category--hotel" },
    ],
  ],
};
