import { Component, OnInit } from '@angular/core';

type Indicator = {
  id: number;
  name: string;
};

@Component({
  selector: 'pnx-calc-module',
  templateUrl: './module.component.html',
  styleUrls: ['./module.component.css'],
})
export class ModuleComponent implements OnInit {
  description: string;
  titleModule: string;
  indicators: Array<Indicator> = [];

  constructor() {}

  ngOnInit() {
    this.titleModule = 'Calculatrice';
    this.description = "C'est le module calculatrice";
    this.indicators = [
      { id: 1, name: 'foo' },
      { id: 2, name: 'bar' },
    ];
  }
}
